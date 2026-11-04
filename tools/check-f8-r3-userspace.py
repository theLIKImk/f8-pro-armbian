"""Verify R3's newly included ARM64 blkid runtime offline; no device access."""
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import stat
import subprocess

P=Path(__file__).resolve().parents[1]
out=P/'outputs/armbian/firstboot-diagnostic-r3'
work=Path('/var/tmp/f8-pro-armbian/firstboot-diagnostic-r3/blkid-runtime-check')
work.mkdir(exist_ok=True)
spec=importlib.util.spec_from_file_location('usb_builder',P/'tools/build-usb-bootlog.py')
helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
ramdisk=out/'initramfs-diagnostic.cpio.gz'
records=helper.cpio_read(gzip.decompress(ramdisk.read_bytes()))
for name,fields,data in records:
    if name in ['lib','lib64','sbin'] or name.startswith(('lib/','lib64/','sbin/')):
        target=work/name
        if stat.S_ISDIR(fields[1]):target.mkdir(parents=True,exist_ok=True)
        else:
            assert stat.S_ISREG(fields[1]),'Unexpected dynamic-runtime symlink'
            target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data);target.chmod(fields[1]&0o777)
version=subprocess.check_output(['qemu-aarch64-static','-L',str(work),str(work/'sbin/blkid'),'--version'],text=True)
assert version.startswith('blkid ')
init=next(data for name,_,data in records if name=='init')
assert b'mount -t ext4 -o ro,noload /dev/mmcblk0p6 /run/original-root' in init
assert b'614e0000-0000-4b53-8000-1d28000054a9' in init
assert b'timeout 10 chroot /run/original-root /usr/lib/systemd/systemd --version' in init
assert b'switch_root' not in init and b' -o rw' not in init
report={'scope':'Offline QEMU ARM64 blkid runtime and packed-init policy check; no mount or target process execution',
        'ramdisk_sha256':hashlib.sha256(ramdisk.read_bytes()).hexdigest(),
        'blkid_version':version.strip(),'dynamic_dependencies_execute_under_qemu':True,
        'root_partuuid_guard_present':True,'readonly_noload_mount_present':True,
        'systemd_version_only_with_timeout':True,'switch_root_absent':True,
        'original_arch_userspace_executed':False}
(out/'userspace-precheck.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
