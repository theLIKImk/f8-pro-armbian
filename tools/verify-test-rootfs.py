"""Verify the candidate offline; do not start network, SSH, or hardware services."""
import json
from pathlib import Path
import subprocess

project = Path(__file__).resolve().parent.parent
root = Path('/var/tmp/f8-pro-archlinux-20261027/rootfs-vendor-staging')
output = project / 'analysis/test-rootfs'


def target(*args):
    result = subprocess.run(['chroot', str(root), *args], capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError('Target check failed: {}\n{}'.format(args[0], result.stdout + result.stderr))
    return result.stdout


subprocess.run(['python3', str(project / 'tools/test-board-settings.py')], check=True)
units = ('f8-pro-wifi.service', 'f8-pro-bluetooth.service', 'f8-pro-keyring.service')
unit_check = subprocess.run(['chroot', str(root), '/usr/bin/systemd-analyze', 'verify', *units], capture_output=True, text=True)
(output / 'systemd-unit-check.txt').write_text(unit_check.stdout + unit_check.stderr)
if unit_check.returncode:
    raise RuntimeError('Unit verification failed; inspect systemd-unit-check.txt')
subprocess.run(['systemctl', '--root', str(root), 'is-enabled', 'NetworkManager', 'sshd', *units], check=True)
if not (root / 'usr/lib/systemd/system/sshdgenkeys.service').is_file():
    raise RuntimeError('No first-boot SSH host-key generator')
if 'sshdgenkeys.service' not in (root / 'usr/lib/systemd/system/sshd.service').read_text():
    raise RuntimeError('SSH host key generation is not ordered before sshd')
# Temporary host keys exist only for validation and are always removed afterward.
try:
    target('/usr/bin/ssh-keygen', '-A')
    target('/usr/bin/sshd', '-t')
    config = target('/usr/bin/sshd', '-T')
    (output / 'sshd-effective-config.txt').write_text(config)
    for required in ('passwordauthentication no', 'kbdinteractiveauthentication no',
                     'permitrootlogin no', 'pubkeyauthentication yes', 'usepam yes'):
        if required not in config.lower().splitlines():
            raise RuntimeError('SSH configuration requirement failed: ' + required)
finally:
    for path in (root / 'etc/ssh').glob('ssh_host_*_key*'):
        if path.is_file() or path.is_symlink():
            path.unlink()
shadow = {line.split(':')[0]: line.split(':')[1] for line in (root / 'etc/shadow').read_text().splitlines()}
assert all(shadow[name].startswith(('!', '*')) for name in ('root', 'alarm'))
assert (root / 'etc/machine-id').read_bytes() == b''
assert not list((root / 'etc/ssh').glob('ssh_host_*_key'))
public = root / 'home/alarm/.ssh/authorized_keys'
assert public.stat().st_mode & 0o777 == 0o600
assert public.stat().st_uid == 1000
record = {
    'offline_unit_validation_passed': True,
    'ssh_key_only_configuration_passed': True,
    'default_passwords_locked': True,
    'host_keys_removed_for_first_boot': True,
    'machine_id_empty_for_first_boot': True,
    'bluetooth_address_and_network_profile_tests_passed': True,
    'target_nm_version': target('/usr/bin/NetworkManager', '--version').strip(),
    'target_python_version': target('/usr/bin/python', '--version').strip(),
    'hardware_boot_tested': False,
}
(output / 'verification.json').write_text(json.dumps(record, indent=2) + '\n')
print('PASS: unit ordering, SSH configuration, locked passwords, fresh host identity and target program checks')
