"""Extract verified official packages for inspection; never run maintainer scripts."""
import hashlib
import json
from pathlib import Path
import subprocess

PROJECT = Path('/mnt/d/Netdisk/Other/F8-PRO/archlinux')
records = json.loads((PROJECT / 'analysis/armbian/repository/downloaded-kernel-packages.json').read_text())
root = Path('/var/tmp/f8-pro-armbian/official-kernel')
root.mkdir(parents=True, exist_ok=True)
for record in records:
    archive = PROJECT / record['file'].replace('\\', '/')
    assert hashlib.file_digest(archive.open('rb'), 'sha256').hexdigest() == record['sha256']
    subprocess.run(['dpkg-deb', '--extract', str(archive), str(root)], check=True)
configs = list((root / 'boot').glob('config-*'))
assert len(configs) == 1
config = dict(line.split('=', 1) for line in configs[0].read_text().splitlines() if line.startswith('CONFIG_') and '=' in line)
keys = ['DRM_PANTHOR', 'BATTERY_CW2015', 'CHARGER_BQ25890', 'MFD_RK806_SPI', 'REGULATOR_RK860X',
        'SQUASHFS', 'OVERLAY_FS', 'BLK_DEV_LOOP', 'EXT4_FS', 'MODULES', 'MODVERSIONS']
modules = list(root.glob('usr/lib/modules/*')) or list(root.glob('lib/modules/*'))
assert len(modules) == 1
panthor = list(modules[0].rglob('panthor.ko*'))
headers = list((root / 'usr/src').glob('linux-headers-*'))
images = [x for x in (root / 'boot').glob('vmlinuz-*') if x.is_file()]
report = {'scope': 'Extracted only; no package scripts, module loading, boot writes or target installation',
          'official_release': modules[0].name, 'headers': [str(x) for x in headers],
          'config': {key: config.get('CONFIG_' + key, 'n') for key in keys},
          'panthor_modules': [str(x) for x in panthor],
          'images': [{'path': str(x), 'bytes': x.stat().st_size,
                      'sha256': hashlib.file_digest(x.open('rb'), 'sha256').hexdigest()} for x in images]}
(PROJECT / 'analysis/armbian/repository/extracted-kernel-report.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
