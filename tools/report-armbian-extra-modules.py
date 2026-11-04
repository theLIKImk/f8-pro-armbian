"""Verify official-ABI extra modules and stage reviewable, not installed artifacts."""
import hashlib
import json
from pathlib import Path
import shutil
import struct
import subprocess

P = Path('/mnt/d/Netdisk/Other/F8-PRO/archlinux')
W = Path('/var/tmp/f8-pro-armbian/extra-modules-6.1.115')
release = '6.1.115-vendor-rk35xx'
out = P / 'outputs/armbian/extra-modules-6.1.115'
records = []
for name in ['cw2015_battery', 'bq25890_charger']:
    module = W / (name + '.ko')
    data = module.read_bytes()
    assert data[:6] == b'\x7fELF\x02\x01' and struct.unpack_from('<H', data, 18)[0] == 183
    magic = subprocess.check_output(['modinfo', '-F', 'vermagic', str(module)], text=True).strip()
    assert magic.startswith(release + ' ') and 'modversions' in magic, magic
    versions = subprocess.check_output(['modprobe', '--show-modversions', str(module)], text=True)
    assert 'module_layout' in versions
    records.append({'name': name, 'vermagic': magic, 'bytes': len(data),
                    'sha256': hashlib.sha256(data).hexdigest(), 'versioned_symbols': len(versions.splitlines())})
out.mkdir(parents=True, exist_ok=True)
for record in records:
    shutil.copy2(W / (record['name'] + '.ko'), out)
result = {'official_release': release, 'modules': records,
          'scope': 'Built/modpost/ELF/vermagic/version-symbol checks only; not loaded or hardware-tested',
          'source_note': 'Driver C sources audited at 85233a85; compiled using exact official 6.1.115 headers and Module.symvers'}
(P / 'analysis/armbian/extra-modules/verified-modules.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
