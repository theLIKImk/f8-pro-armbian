"""Build an independent USB log initramfs with unchanged factory kernel/DTB.

Never flashes hardware. Original factory recovery startup is NOT executed.
"""
import argparse
import gzip
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import stat
import subprocess

PROJECT = Path(__file__).resolve().parent.parent
BASE = Path('/var/tmp/f8-pro-archlinux-20261027')
WORK = BASE / 'usb-bootlog-build-20261028-r3'
EXPORT = BASE / 'exports/usb-bootlog-r3'


def run(argv, cwd=None):
    r = subprocess.run(argv, cwd=cwd, capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError(f'{argv[0]}: {r.stderr[-1500:]}')
    return r.stdout


def sha(data):
    return hashlib.sha256(data).hexdigest()


def cpio_read(data):
    records = []
    p = 0
    while p + 110 <= len(data):
        h = data[p:p+110]
        if h[:6] not in (b'070701', b'070702'):
            raise RuntimeError('Unexpected cpio encoding')
        values = [int(h[6+i*8:14+i*8], 16) for i in range(13)]
        size, namesize = values[6], values[11]
        name = data[p+110:p+110+namesize-1].decode()
        p = (p+110+namesize+3) & ~3
        payload = data[p:p+size]
        p = (p+size+3) & ~3
        if name == 'TRAILER!!!':
            return records
        if not name or name.startswith('/') or '..' in name.split('/') or len(payload) != size:
            raise RuntimeError('Unsafe or truncated archive record')
        records.append((name, values, payload))
    raise RuntimeError('Missing cpio trailer')


def cpio_write(records):
    out = bytearray()
    for name, values, payload in records + [('TRAILER!!!', [0]*13, b'')]:
        namebytes = name.encode() + b'\0'
        values = values.copy()
        values[6], values[11], values[12] = len(payload), len(namebytes), 0
        out += b'070701' + ''.join(f'{v:08x}' for v in values).encode() + namebytes
        out += b'\0' * (-len(out) % 4)
        out += payload
        out += b'\0' * (-len(out) % 4)
    out += b'\0' * (-len(out) % 512)
    return bytes(out)


def main():
    global WORK, EXPORT
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--handoff', action='store_true', help='Boot actual Arch PID1 and snapshot logs')
    parser.add_argument('--wifi-fix', action='store_true', help='Apply the tested Wi-Fi MAC workaround before handoff')
    parser.add_argument('--normal', action='store_true', help='Normal Arch boot without diagnostic helpers')
    args = parser.parse_args()
    if args.wifi_fix and not args.handoff:
        parser.error('--wifi-fix requires --handoff')
    if args.normal and (args.handoff or args.wifi_fix):
        parser.error('--normal cannot be combined with diagnostic modes')
    if args.handoff:
        WORK = BASE / 'usb-handoff-build-20261028-r5'
        EXPORT = BASE / 'exports/usb-handoff-r5'
    if args.wifi_fix:
        WORK = BASE / 'usb-handoff-build-20261028-r6-macfix'
        EXPORT = BASE / 'exports/usb-handoff-r6-macfix'
    if args.normal:
        WORK = BASE / 'normal-boot-build-20261028-v1'
        EXPORT = BASE / 'exports/normal-boot-v1'
    os.umask(0o077)
    if os.getuid() != 0 or WORK.exists() or EXPORT.exists():
        raise RuntimeError('Requires root and unused diagnostic output paths')
    spec = importlib.util.spec_from_file_location('f8_images', PROJECT/'tools/inspect_images.py')
    images = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(images)
    source = PROJECT/'vendor/ubuntu-5.10.160/boot-assets/recovery.img'
    original = source.read_bytes()
    nodes = images.fdt(original)
    inputs = {}
    for name in ('fdt', 'kernel', 'ramdisk', 'resource'):
        node = nodes['/images/'+name]
        offset = int.from_bytes(node['data-position'], 'big')
        size = int.from_bytes(node['data-size'], 'big')
        data = original[offset:offset+size]
        if len(data) != size or bytes.fromhex(sha(data)) != nodes['/images/'+name+'/hash']['value']:
            raise RuntimeError('Factory FIT payload hash mismatch')
        inputs[name] = data
    records = cpio_read(gzip.decompress(inputs['ramdisk']))
    names = {r[0] for r in records}
    if not {'init', 'usr/bin/busybox', 'usr/bin/mount', 'usr/sbin/losetup'} <= names:
        raise RuntimeError('Factory ramdisk is missing expected tools')
    WORK.mkdir(mode=0o700)
    EXPORT.mkdir(mode=0o700)
    monitor = WORK/'f8-monitor'
    if not args.normal:
        run(['aarch64-linux-gnu-gcc', '-static', '-O2', '-Wall', '-Wextra', '-Werror',
             str(PROJECT/'tools/early-init-diagnostic.c'), '-o', str(monitor)])
        run(['qemu-aarch64-static', str(monitor), '--self-test'])
    init_name = 'normal-boot-init.sh' if args.normal else ('usb-handoff-init.sh' if args.handoff else 'usb-bootlog-init.sh')
    init_source = PROJECT/'tools'/init_name
    run(['sh', '-n', str(init_source)])
    if args.handoff:
        run(['sh', '-n', str(PROJECT/'tools/usb-handoff-snapshot.sh')])
    fat = WORK/'f8-logs.img'
    if not args.normal:
        with fat.open('xb') as f:
            f.truncate(64*1024**2)
        run(['mkfs.vfat', '-F', '16', '-n', 'F8BOOTLOG', str(fat)])
    init = init_source.read_bytes().replace(b'\r\n', b'\n')
    # Do not ship executable automatic recovery paths in the diagnostic ramdisk.
    excluded = {'init', 'usr/bin/recovery', 'etc/init.d/S40recovery'}
    if args.normal:
        excluded.update({'usr/bin/adbd', 'usr/bin/usbdevice', 'etc/inittab', 'etc/fstab'})
    records = [r for r in records if r[0] not in excluded and
               not (args.normal and (r[0] == 'etc/init.d' or r[0].startswith('etc/init.d/')))]
    ino = max(r[1][0] for r in records)+1
    extra = [('init', init, 0o755)]
    if not args.normal:
        extra += [('f8-monitor', monitor.read_bytes(), 0o755), ('f8-logs.img', fat.read_bytes(), 0o600)]
    if args.handoff:
        extra.append(('f8-snapshot.sh', (PROJECT/'tools/usb-handoff-snapshot.sh').read_bytes().replace(b'\r\n', b'\n'), 0o700))
    if args.wifi_fix:
        extra.append(('f8-wifi-fix.py', (PROJECT/'tools/fix-wifi-mac.py').read_bytes().replace(b'\r\n', b'\n'), 0o600))
    for name, data, mode in extra:
        values = [ino, stat.S_IFREG | mode, 0, 0, 1, 0, len(data), 0, 0, 0, 0, len(name)+1, 0]
        records.append((name, values, data))
        ino += 1
    archive = cpio_write(records)
    checked = {r[0]: r[2] for r in cpio_read(archive)}
    if checked['init'] != init or 'usr/bin/recovery' in checked:
        raise RuntimeError('Repacked initramfs verification failed')
    if args.normal:
        if any(name.startswith('f8-') or name.startswith('etc/init.d/') for name in checked):
            raise RuntimeError('Diagnostic payload or recovery startup left in normal image')
        if any(word in init for word in (b'--log-level=debug', b'usb_gadget', b'f8diag')):
            raise RuntimeError('Diagnostic initialization remains in normal init')
    elif checked['f8-monitor'] != monitor.read_bytes():
        raise RuntimeError('Diagnostic monitor mismatch')
    ramdisk = gzip.compress(archive, compresslevel=6, mtime=0)
    for name in ('fdt', 'kernel', 'resource'):
        (WORK/name).write_bytes(inputs[name])
    (WORK/'ramdisk').write_bytes(ramdisk)
    its = '''/dts-v1/;
/ {
 description = "F8-PRO read-only USB boot log diagnostic";
 #address-cells = <1>;
 images {
  fdt { data = /incbin/("fdt"); type = "flat_dt"; arch = "arm64";
   compression = "none"; load = <0xffffff00>; hash { algo = "sha256"; }; };
  kernel { data = /incbin/("kernel"); type = "kernel"; arch = "arm64"; os = "linux";
   compression = "none"; load = <0xffffff01>; entry = <0xffffff01>; hash { algo = "sha256"; }; };
  ramdisk { data = /incbin/("ramdisk"); type = "ramdisk"; arch = "arm64"; os = "linux";
   compression = "none"; load = <0xffffff02>; hash { algo = "sha256"; }; };
  resource { data = /incbin/("resource"); type = "multi"; arch = "arm64";
   compression = "none"; hash { algo = "sha256"; }; };
 };
 configurations { default = "conf"; conf { rollback-index = <0>;
  kernel = "kernel"; fdt = "fdt"; ramdisk = "ramdisk"; multi = "resource"; }; };
};
'''
    if args.normal:
        its = its.replace('F8-PRO read-only USB boot log diagnostic', 'F8-PRO normal Arch initramfs boot')
    (WORK/'boot.its').write_text(its)
    output = EXPORT/('f8-pro-normal-boot.img' if args.normal else 'f8-pro-usb-bootlog-boot.img')
    listing = run(['mkimage', '-E', '-p', '0x800', '-f', 'boot.its', str(output)], cwd=WORK)
    (EXPORT/'fit-list.txt').write_text(listing)
    result = output.read_bytes()
    if len(result) > 64*1024**2:
        raise RuntimeError('Diagnostic FIT exceeds the original boot partition')
    checked = images.fdt(result)
    for name in ('fdt', 'kernel', 'ramdisk', 'resource'):
        node = checked['/images/'+name]
        start = int.from_bytes(node['data-position'], 'big')
        length = int.from_bytes(node['data-size'], 'big')
        data = result[start:start+length]
        if bytes.fromhex(sha(data)) != checked['/images/'+name+'/hash']['value']:
            raise RuntimeError('Generated FIT payload hash mismatch')
        if data != (ramdisk if name == 'ramdisk' else inputs[name]):
            raise RuntimeError('Factory payload unexpectedly changed')
    record = {
        'variant': 'normal-boot' if args.normal else ('usb-arch-handoff' if args.handoff else 'usb-bootlog-boot'),
        'size_bytes': len(result), 'sha256': sha(result),
        'factory_recovery_sha256': sha(original), 'factory_kernel_unchanged': True,
        'factory_dtb_unchanged': True, 'factory_resource_unchanged': True,
        'static_monitor_self_test': None if args.normal else True, 'cpio_roundtrip_checked': True,
        'fit_payloads_checked': True, 'fat_volume_bytes': 0 if args.normal else 64*1024**2,
        'rootfs_mount_options': 'rw for real Arch boot' if args.handoff or args.normal else 'ro,noload',
        'arch_pid1_handoff': args.handoff or args.normal, 'automatic_recovery_removed': True,
        'diagnostic_helpers_present': not args.normal,
        'wifi_mac_fix_before_handoff': args.wifi_fix,
        'partition': 'boot', 'start_lba': '0x00008000', 'rootfs_not_flashed': True,
        'fit_signature': 'No new signature generated; target acceptance untested',
        'hardware_boot_tested': False, 'usb_enumeration_tested': False,
        'warning': 'BOOT partition test image, not rootfs and not RKFW update firmware'
    }
    (EXPORT/'manifest.json').write_text(json.dumps(record, indent=2)+'\n')
    (EXPORT/'SHA256SUMS').write_text(record['sha256']+'  '+output.name+'\n')
    print(json.dumps(record), flush=True)


if __name__ == '__main__':
    main()
