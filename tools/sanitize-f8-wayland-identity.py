"""Remove unused build-generated host keys; generate fresh target keys before SSH."""
import fcntl
import json
from pathlib import Path
import shutil
import subprocess

P = Path(__file__).resolve().parents[1]
B = Path('/var/tmp/f8-pro-armbian')
ROOT = B / 'rootfs-trixie-wayland'
lock = (B / 'wayland-install.lock').open('a')
fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
assert (B / 'wayland-packages-installed.ok').is_file()
assert (ROOT / 'etc/f8-pro-evaluation').is_file()
assert (ROOT / 'usr/bin/ssh-keygen').is_file()
unit_name = 'f8-pro-ssh-hostkeys.service'
unit = ROOT / 'usr/lib/systemd/system' / unit_name
shutil.copy2(P / 'armbian/rootfs-overlay/usr/lib/systemd/system' / unit_name, unit)
requires = ROOT / 'etc/systemd/system/ssh.service.requires'
requires.mkdir(parents=True, exist_ok=True)
link = requires / unit_name
if link.is_symlink():
    assert str(link.readlink()) == '/usr/lib/systemd/system/' + unit_name
else:
    assert not link.exists()
    link.symlink_to('/usr/lib/systemd/system/' + unit_name)
result = subprocess.run(['systemd-analyze', '--root=' + str(ROOT), '--man=no', 'verify', unit_name],
                        capture_output=True, text=True)
assert result.returncode == 0, result.stdout + result.stderr
removed = []
for algorithm in ['rsa', 'ecdsa', 'ed25519']:
    for suffix in ['', '.pub']:
        path = ROOT / ('etc/ssh/ssh_host_' + algorithm + '_key' + suffix)
        assert path.resolve().is_relative_to(ROOT.resolve()) and not path.is_symlink()
        if path.exists():
            assert path.is_file()
            path.unlink()
            removed.append(path.name)
identity = ROOT / 'etc/machine-id'
assert identity.resolve().is_relative_to(ROOT.resolve()) and not identity.is_symlink()
identity.write_text('')
dbus = ROOT / 'var/lib/dbus/machine-id'
if dbus.exists() and not dbus.is_symlink():
    assert dbus.resolve().is_relative_to(ROOT.resolve())
    dbus.write_text('')
report = {'scope': 'Only unused isolated-build identity sanitized; no original tablet or SSH client keys touched',
          'removed_build_key_filenames': removed, 'machine_id_empty': True,
          'target_hostkey_unit_verified': True, 'ssh_requires_hostkey_generation': True,
          'first_boot_service_executed': False,
          'note': 'RAM-overlay evaluations generate ephemeral host keys each boot; persistent identity is pending the final storage design'}
(P / 'analysis/armbian/userspace/identity-sanitization.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
