"""Offline ABI-specific initramfs candidate. Never creates a FIT or accesses a device."""
import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import struct
import subprocess
import tempfile

P = Path(__file__).resolve().parents[1]
B = Path('/var/tmp/f8-pro-armbian')
parser = argparse.ArgumentParser()
parser.add_argument('--custom', action='store_true', help='Use verified custom 6.1.172 desktop snapshot')
args = parser.parse_args()
ROOT = B / ('rootfs-trixie-wayland' if args.custom else 'rootfs-trixie-evaluation')
RELEASE = '6.1.172-f8-pro-armbian-eval' if args.custom else '6.1.115-vendor-rk35xx'
OUT = P / ('outputs/armbian/evaluation-initramfs-custom' if args.custom else 'outputs/armbian/evaluation-initramfs')
REPORT = P / ('analysis/armbian/initramfs/custom' if args.custom else 'analysis/armbian/initramfs')
OUT.mkdir(parents=True, exist_ok=True)
REPORT.mkdir(parents=True, exist_ok=True)


def run(*args):
    return subprocess.check_output(args, text=True).strip()


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


config = ((B / 'kernel-config-build/.config') if args.custom else
          (B / 'official-kernel/boot' / ('config-' + RELEASE))).read_text()
for key in ['BLK_DEV_INITRD', 'RD_GZIP', 'DEVTMPFS', 'BLK_DEV_LOOP', 'MMC_BLOCK',
            'MMC_SDHCI_OF_DWCMSHC', 'EFI_PARTITION', 'EXT4_FS', 'SQUASHFS_ZLIB']:
    assert f'CONFIG_{key}=y\n' in config, key
filesystem_modules = []
for symbol, module in [('SQUASHFS', 'squashfs'), ('OVERLAY_FS', 'overlay')]:
    assert f'CONFIG_{symbol}=y\n' in config or f'CONFIG_{symbol}=m\n' in config
    if f'CONFIG_{symbol}=m\n' in config:
        filesystem_modules.append(module)
if args.custom:
    assert not filesystem_modules
    kernel_report = json.loads((P / 'analysis/armbian/kernel-build/verified-evaluation-image.json').read_text())
    assert kernel_report['release'] == RELEASE
    assert (B / 'kernel-config-build/include/config/kernel.release').read_text().strip() == RELEASE
    expected_files = {item['name']: item['sha256'] for item in kernel_report['files']}
    assert sha(B / 'kernel-config-build/.config') == expected_files['evaluation.config']
    assert sha(P / 'outputs/armbian/evaluation-kernel/Image') == expected_files['Image']
assert 'CONFIG_MODULE_SIG_FORCE=y' not in config

packages = list((B / 'rootfs-trixie-evaluation/var/tmp/f8-initramfs-packages').glob('busybox-static_*_arm64.deb'))
assert len(packages) == 1, packages
package = packages[0]
version = run('dpkg-deb', '-f', str(package), 'Version')
assert run('dpkg-deb', '-f', str(package), 'Architecture') == 'arm64'
metadata = run('chroot', str(ROOT), 'apt-cache', 'show', 'busybox-static:arm64')
records = []
for paragraph in metadata.split('\n\n'):
    record = dict(line.split(': ', 1) for line in paragraph.splitlines()
                  if ': ' in line and not line.startswith(' '))
    if record.get('Version') == version:
        records.append(record)
assert len(records) == 1 and sha(package) == records[0]['SHA256']
(REPORT / 'busybox-apt-record.txt').write_text(metadata + '\n')

image = P / ('outputs/armbian/evaluation-wayland/rootfs.squashfs' if args.custom else
             'outputs/armbian/evaluation-core/rootfs.squashfs')
root_report = json.loads((P / ('analysis/armbian/userspace/verified-wayland-squashfs.json' if args.custom else
                              'analysis/armbian/userspace/verified-evaluation-core.json')).read_text())
assert sha(image) == root_report['sha256'] and root_report['module_release'] == RELEASE
init = P / 'armbian/initramfs/evaluation-init.sh'
subprocess.run(['sh', '-n', str(init)], check=True)

with tempfile.TemporaryDirectory(prefix='initramfs-', dir=B) as temp:
    work = Path(temp)
    tree, extracted = work / 'tree', work / 'package'
    subprocess.run(['dpkg-deb', '-x', str(package), str(extracted)], check=True)
    for directory in ['bin', 'sbin', 'etc', 'proc', 'sys', 'dev', 'run', 'mnt/root', 'lib/modules']:
        (tree / directory).mkdir(parents=True, exist_ok=True)
    busybox_path = extracted / 'usr/bin/busybox'
    assert busybox_path.is_file() and not busybox_path.is_symlink()
    busybox = busybox_path.read_bytes()
    assert busybox[:6] == b'\x7fELF\x02\x01' and struct.unpack_from('<H', busybox, 18)[0] == 183
    phoff = struct.unpack_from('<Q', busybox, 32)[0]
    phentsize, phnum = struct.unpack_from('<HH', busybox, 54)
    assert all(struct.unpack_from('<I', busybox, phoff + n * phentsize)[0] != 3
               for n in range(phnum)), 'BusyBox must have no dynamic PT_INTERP'
    shutil.copy2(busybox_path, tree / 'bin/busybox')
    apps = set(run('qemu-aarch64-static', str(tree / 'bin/busybox'), '--list').splitlines())
    needed = ['sh', 'mount', 'mkdir', 'cat', 'sleep', 'sha256sum', 'switch_root', 'modprobe', 'uname']
    assert set(needed) <= apps
    for name in needed:
        (tree / 'bin' / name).symlink_to('busybox')
    # Debian's static BusyBox has no blkid applet. Copy the target util-linux
    # binary and resolve its ELF dependencies from this isolated ARM64 root.
    dynamic_files = []
    pending = [(ROOT / 'usr/sbin/blkid', Path('sbin/blkid'))]
    seen = set()
    while pending:
        source, relative = pending.pop()
        if relative in seen:
            continue
        seen.add(relative)
        assert source.resolve().is_relative_to(ROOT.resolve()), source
        content = source.read_bytes()
        assert content[:6] == b'\x7fELF\x02\x01' and struct.unpack_from('<H', content, 18)[0] == 183
        destination = tree / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
        destination.chmod(0o755)
        dynamic_files.append({'path': str(relative), 'sha256': sha(source)})
        dynamic = run('readelf', '-d', str(source))
        for library in re.findall(r'\(NEEDED\).*\[(.*?)\]', dynamic):
            candidate = ROOT / 'usr/lib/aarch64-linux-gnu' / library
            assert candidate.is_file(), library
            pending.append((candidate, Path('lib/aarch64-linux-gnu') / library))
        interpreter = re.search(r'Requesting program interpreter: (.*?)\]', run('readelf', '-l', str(source)))
        if interpreter:
            relative_interpreter = Path(interpreter[1].lstrip('/'))
            # Resolve the ARM64 root's absolute /lib symlink inside its root,
            # never against the host's library directory.
            interpreter_source = ROOT / 'usr/lib/aarch64-linux-gnu' / relative_interpreter.name
            assert interpreter_source.is_file()
            pending.append((interpreter_source, relative_interpreter))
    assert run('qemu-aarch64-static', '-L', str(tree), str(tree / 'sbin/blkid'), '--version').startswith('blkid ')
    shutil.copy2(init, tree / 'init')
    (tree / 'init').chmod(0o755)
    (tree / 'etc/f8-evaluation.release').write_text(RELEASE + '\n')
    (tree / 'etc/f8-evaluation.sha256').write_text(root_report['sha256'] + '  rootfs.squashfs\n')
    os.mknod(tree / 'dev/console', stat.S_IFCHR | 0o600, os.makedev(5, 1))
    os.mknod(tree / 'dev/null', stat.S_IFCHR | 0o666, os.makedev(1, 3))
    module_report = []
    module_root = ROOT / 'lib/modules' / RELEASE
    target_modules = tree / 'lib/modules' / RELEASE
    for module in filesystem_modules:
        dependencies = run('modprobe', '-d', str(ROOT), '-S', RELEASE, '--show-depends', module)
        for line in dependencies.splitlines():
            assert line.startswith('insmod '), line
            source = Path(line.split()[1])
            relative = source.relative_to(module_root)
            vermagic = run('modinfo', '-F', 'vermagic', str(source))
            assert vermagic.split()[0] == RELEASE
            destination = target_modules / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
            module_report.append({'path': str(relative), 'sha256': sha(source), 'vermagic': vermagic})
    if filesystem_modules:
        for pattern in ['modules.builtin*', 'modules.order']:
            for source in module_root.glob(pattern):
                shutil.copy2(source, target_modules / source.name)
        subprocess.run(['depmod', '-b', str(tree), '-a', RELEASE], check=True)
    # Ask the target BusyBox to resolve both modules without loading them.
    # Its modprobe has no alternate-root/release flags; QEMU supplies uname -r
    # and chroot supplies the filesystem. This temporary host helper is omitted.
    shutil.copy2('/usr/bin/qemu-aarch64-static', tree / 'qemu-host')
    for module in filesystem_modules:
        resolved = run('chroot', str(tree), '/qemu-host', '-r', RELEASE,
                       '/bin/busybox', 'modprobe', '-D', module)
        assert module + '.ko' in resolved, resolved
    (tree / 'qemu-host').unlink()
    paths = sorted(['.'] + [str(path.relative_to(tree)) for path in tree.rglob('*')])
    packed = subprocess.run(['cpio', '--null', '-o', '--format=newc', '--owner=0:0', '--reproducible'],
                            cwd=tree, input=('\0'.join(paths) + '\0').encode(),
                            capture_output=True, check=True).stdout
    # Parse the actual archive, checking contents, symlinks and device nodes.
    entries, offset = {}, 0
    while True:
        header = packed[offset:offset + 110]
        assert header[:6] == b'070701'
        fields = [int(header[n:n + 8], 16) for n in range(6, 110, 8)]
        size, namesize = fields[6], fields[11]
        name = packed[offset + 110:offset + 110 + namesize - 1].decode()
        offset = (offset + 110 + namesize + 3) & ~3
        data = packed[offset:offset + size]
        offset = (offset + size + 3) & ~3
        if name == 'TRAILER!!!':
            break
        entries[name] = (fields, data)
        assert fields[2] == fields[3] == 0
        path = tree / name
        if path.is_symlink():
            assert data.decode() == os.readlink(path)
        elif path.is_file():
            assert data == path.read_bytes()
    assert entries['init'][1] == init.read_bytes()
    assert entries['dev/console'][0][9:11] == [5, 1]
    assert entries['dev/null'][0][9:11] == [1, 3]
    if args.custom:
        assert not list(tree.rglob('*.ko'))
    output = OUT / ('initramfs-' + ('6.1.172-custom' if args.custom else '6.1.115') + '-DO-NOT-BOOT.cpio.gz')
    output.write_bytes(gzip.compress(packed, compresslevel=9, mtime=0))

kernel = (P / 'outputs/armbian/evaluation-kernel/Image') if args.custom else (B / 'official-kernel/boot' / ('vmlinuz-' + RELEASE))
report = {'scope': 'Offline archive/ABI/dependency checks only; no board DTB/FIT or runtime validation',
          'release': RELEASE, 'busybox_version': version, 'busybox_deb_sha256': sha(package),
          'busybox_static_aarch64': True, 'target_module_resolution_passed': True if filesystem_modules else None,
          'module_resolution_applicable': bool(filesystem_modules),
          'filesystems_builtin': args.custom,
          'blkid_target_runtime_verified': True, 'blkid_files': dynamic_files,
          'modules': module_report, 'archive_entries': len(entries), 'archive_bytes': output.stat().st_size,
          'archive_sha256': sha(output), 'rootfs_sha256': sha(image),
          'init_script_sha256': sha(init),
          'kernel_image_bytes': kernel.stat().st_size,
          'kernel_source_kind': 'custom-evaluation' if args.custom else 'official-package',
          'image_plus_initramfs_bytes': kernel.stat().st_size + output.stat().st_size,
          'boot_partition_bytes': 64 * 1024 * 1024,
          'note': 'Size subtotal excludes FIT metadata/DTB/alignment. Board support remains incomplete.'}
(REPORT / 'verified-initramfs.json').write_text(json.dumps(report, indent=2) + '\n')
(OUT / 'SHA256SUMS').write_text(sha(output) + '  ' + output.name + '\n')
print(json.dumps(report, indent=2))
