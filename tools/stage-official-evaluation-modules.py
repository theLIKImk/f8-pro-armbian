"""Stage matching official modules into the isolated evaluation root, never live /lib."""
import json
from pathlib import Path
import shutil
import subprocess

P = Path('/mnt/d/Netdisk/Other/F8-PRO/archlinux')
B = Path('/var/tmp/f8-pro-armbian')
root = B / 'rootfs-trixie-evaluation'
assert (B / 'evaluation-core.ok').is_file()
assert (root / 'etc/f8-pro-evaluation').is_file()
release = '6.1.115-vendor-rk35xx'
config = (B / 'official-kernel/boot' / ('config-' + release)).read_text()
assert 'CONFIG_MODULE_SIG_FORCE=y' not in config
target = root / 'lib/modules' / release
assert target.resolve().is_relative_to(root.resolve())
shutil.copytree(B / 'official-kernel/lib/modules' / release, target, dirs_exist_ok=True, symlinks=True)
for name in ['build', 'source']:
    path = target / name
    if path.is_symlink():
        path.unlink()
verified = json.loads((P / 'analysis/armbian/extra-modules/verified-modules.json').read_text())
assert verified['official_release'] == release
extra = target / 'updates/f8-pro'
extra.mkdir(parents=True, exist_ok=True)
for item in verified['modules']:
    shutil.copy2(P / 'outputs/armbian/extra-modules-6.1.115' / (item['name'] + '.ko'), extra)
subprocess.run(['depmod', '-b', str(root), '-a', release], check=True)
assert 'updates/f8-pro/cw2015_battery.ko' in (target / 'modules.dep').read_text()
assert 'updates/f8-pro/bq25890_charger.ko' in (target / 'modules.dep').read_text()
print('Official 6.1.115 modules and extras staged; depmod completed only in evaluation root')
