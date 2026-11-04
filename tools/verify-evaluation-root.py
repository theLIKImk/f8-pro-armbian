"""Inspect the produced SquashFS without mounting or executing target programs."""
import hashlib
import json
import os
from pathlib import Path
import struct
import subprocess

P = Path('/mnt/d/Netdisk/Other/F8-PRO/archlinux')
toolroot = Path('/var/tmp/f8-pro-armbian/host-tools/root')
tool = toolroot / 'usr/bin/unsquashfs'
env = dict(os.environ, LD_LIBRARY_PATH=f'{toolroot}/usr/lib/x86_64-linux-gnu:{toolroot}/lib/x86_64-linux-gnu')
image = P / 'outputs/armbian/evaluation-core/rootfs.squashfs'


def read(path):
    return subprocess.check_output([str(tool), '-cat', str(image), path], env=env)


binary = read('usr/lib/systemd/systemd')
assert binary[:6] == b'\x7fELF\x02\x01' and struct.unpack_from('<H', binary, 18)[0] == 183
assert read('etc/machine-id') == b''
assert b'F8-PRO' in read('etc/f8-pro-evaluation')
firmware = read('usr/lib/firmware/arm/mali/arch10.8/mali_csffw.bin')
assert len(firmware) > 1024
listing = subprocess.check_output([str(tool), '-ll', str(image)], env=env, text=True)
assert 'ssh_host_ed25519_key' not in listing and 'ssh_host_rsa_key' not in listing
for name in ['cw2015_battery', 'bq25890_charger']:
    assert name + '.ko' in listing
report = {'scope': 'Offline content validation only; minimal core, no desktop/complete board boot',
          'bytes': image.stat().st_size, 'sha256': hashlib.file_digest(image.open('rb'), 'sha256').hexdigest(),
          'systemd_architecture': 'AArch64', 'empty_machine_id': True, 'ssh_host_private_keys_absent': True,
          'mali_firmware_bytes': len(firmware), 'mali_firmware_sha256': hashlib.sha256(firmware).hexdigest(),
          'module_release': '6.1.115-vendor-rk35xx'}
(P / 'analysis/armbian/userspace/verified-evaluation-core.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
