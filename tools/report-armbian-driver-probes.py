"""Record selected cross-compiled objects; these are not installable kernel modules."""
import hashlib
import json
from pathlib import Path
import re
import struct
import subprocess

PROJECT = Path('/mnt/d/Netdisk/Other/F8-PRO/archlinux')
BUILD = Path('/var/tmp/f8-pro-armbian/kernel-config-build')
SOURCE = Path('/var/tmp/f8-pro-armbian/linux-rockchip-config')
objects = ['drivers/power/supply/cw2015_battery.o', 'drivers/power/supply/bq25890_charger.o',
           'drivers/regulator/rk860x-regulator.o', 'drivers/mfd/rk806-core.o',
           'drivers/pinctrl/pinctrl-rk806.o', 'drivers/gpu/drm/panthor/panthor.o']
records = []
for name in objects:
    path = BUILD / name
    data = path.read_bytes()
    assert data[:6] == b'\x7fELF\x02\x01' and struct.unpack_from('<H', data, 18)[0] == 183, name
    records.append({'object': name, 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest(), 'machine': 'AArch64'})
release = re.search(r'"(.*?)"', (BUILD / 'include/generated/utsrelease.h').read_text())[1]
result = {'source_commit': subprocess.check_output(['git', '-C', str(SOURCE), 'rev-parse', 'HEAD'], text=True).strip(),
          'source_release': release, 'compiler': subprocess.check_output(['aarch64-linux-gnu-gcc', '--version'], text=True).splitlines()[0],
          'config_sha256': hashlib.file_digest((BUILD / '.config').open('rb'), 'sha256').hexdigest(),
          'objects': records, 'scope': 'Object build success only. No final .ko/modpost/runtime test. Official 6.1.115 ABI differs.'}
(PROJECT / 'analysis/armbian/kernel-config/driver-probe-report.json').write_text(json.dumps(result, indent=2) + '\n')
print(f'Verified {len(records)} AArch64 objects for {release}')
