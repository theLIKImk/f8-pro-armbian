"""Compare official tablet DTB identities; names alone do not establish F8-PRO support."""
import json
from pathlib import Path
import subprocess

PROJECT = Path('/mnt/d/Netdisk/Other/F8-PRO/archlinux')
root = Path('/var/tmp/f8-pro-armbian/official-kernel/boot/dtb-6.1.115-vendor-rk35xx/rockchip')
out = PROJECT / 'analysis/armbian/repository/tablet-dtbs'
out.mkdir(exist_ok=True)
report = []
for name in ['rk3588s-tablet-v11', 'rk3588s-tablet-v10', 'rk3588s-tablet-rk806-single-v10']:
    path = root / (name + '.dtb')
    model = subprocess.check_output(['fdtget', '-t', 's', str(path), '/', 'model'], text=True).strip()
    compatible = subprocess.check_output(['fdtget', '-t', 's', str(path), '/', 'compatible'], text=True).strip()
    text = subprocess.run(['dtc', '-I', 'dtb', '-O', 'dts', str(path)], capture_output=True, check=True)
    (out / (name + '.dts')).write_bytes(text.stdout)
    (out / (name + '.log')).write_bytes(text.stderr)
    report.append({'dtb': name, 'model': model, 'compatible': compatible,
                   'scope': 'Reference only, not certified for F8-PRO'})
(out / 'identities.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
