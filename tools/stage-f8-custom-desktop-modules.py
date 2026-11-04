"""Attach verified custom modules to the isolated desktop, retaining the old ABI outside it."""
import fcntl
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

P = Path(__file__).resolve().parents[1]
B = Path('/var/tmp/f8-pro-armbian')
ROOT = B / 'rootfs-trixie-wayland'
RELEASE = '6.1.172-f8-pro-armbian-eval'
lock = (B / 'wayland-install.lock').open('a')
fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
assert (ROOT / 'etc/f8-pro-evaluation').is_file()
verified = json.loads((P / 'analysis/armbian/kernel-build/verified-custom-modules.json').read_text())
assert verified['release'] == RELEASE and verified['depmod_symbol_version_check_passed']
manifest = json.loads((P / 'analysis/armbian/kernel-build/custom-modules-manifest.json').read_text())
source = B / 'custom-modules-install/lib/modules' / RELEASE
target = ROOT / 'usr/lib/modules' / RELEASE
assert target.resolve().is_relative_to(ROOT.resolve())
shutil.copytree(source, target, dirs_exist_ok=True, symlinks=True)
for item in manifest:
    path = target / item['path']
    assert path.resolve().is_relative_to(target.resolve())
    with path.open('rb') as stream:
        assert hashlib.file_digest(stream, 'sha256').hexdigest() == item['sha256'], path
assert len(list(target.rglob('*.ko'))) == verified['module_count']
old = ROOT / 'usr/lib/modules/6.1.115-vendor-rk35xx'
retained = B / 'retained-wayland-official-modules/6.1.115-vendor-rk35xx'
if old.exists():
    assert old.resolve().is_relative_to(ROOT.resolve())
    assert retained.resolve().is_relative_to(B.resolve()) and not retained.exists()
    retained.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(old), str(retained))
subprocess.run(['depmod', '-b', str(ROOT), RELEASE], check=True)
result = subprocess.run(['depmod', '-e', '-E', str(B / 'kernel-config-build/Module.symvers'),
                         '-b', str(ROOT), RELEASE], capture_output=True, text=True, check=True)
assert not result.stdout.strip() and not result.stderr.strip(), result.stdout + result.stderr
assert sorted(path.name for path in (ROOT / 'usr/lib/modules').iterdir()) == [RELEASE]
report = {'scope': 'Isolated desktop module staging/CRC verification only; no kernel or module loaded',
          'release': RELEASE, 'verified_module_count': len(manifest), 'module_hashes_matched': True,
          'depmod_symbol_version_check_passed': True, 'prior_official_tree_retained_at': str(retained)}
(P / 'analysis/armbian/userspace/custom-module-staging.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
