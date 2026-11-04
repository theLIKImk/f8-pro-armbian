"""Build and inspect a custom-ABI desktop snapshot, not a deployable board image."""
import fcntl
import hashlib
import json
import os
from pathlib import Path
import struct
import subprocess

P = Path(__file__).resolve().parents[1]
B = Path('/var/tmp/f8-pro-armbian')
ROOT = B / 'rootfs-trixie-wayland'
RELEASE = '6.1.172-f8-pro-armbian-eval'
subprocess.run(['python3', str(P / 'tools/verify-f8-wayland-root.py')], check=True, stdout=subprocess.DEVNULL)
lock = (B / 'wayland-install.lock').open('a')
fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
report = json.loads((P / 'analysis/armbian/userspace/verified-wayland-packages.json').read_text())
assert report['module_releases'] == [RELEASE] and not report['identity_sanitization_required']
for directory in ['proc', 'sys', 'dev', 'run']:
    assert (ROOT / directory).is_dir()
    # util-linux mountpoint returns 32 for an existing non-mountpoint.
    assert subprocess.run(['mountpoint', '-q', str(ROOT / directory)]).returncode == 32, directory
assert (ROOT / 'etc/machine-id').read_bytes() == b''
assert not list((ROOT / 'etc/ssh').glob('ssh_host_*_key'))
assert not [line for line in (ROOT / 'etc/fstab').read_text().splitlines()
            if line.strip() and not line.lstrip().startswith('#')], 'Unexpected fstab mounts'
assert (ROOT / 'etc/systemd/system/ssh.service.requires/f8-pro-ssh-hostkeys.service').is_symlink()
toolroot = B / 'host-tools/root'
env = dict(os.environ, LD_LIBRARY_PATH=f'{toolroot}/usr/lib/x86_64-linux-gnu:{toolroot}/lib/x86_64-linux-gnu')
out = P / 'outputs/armbian/evaluation-wayland'
out.mkdir(parents=True, exist_ok=True)
image = out / 'rootfs.squashfs'
with (B / 'wayland-squashfs.log').open('w') as log:
    subprocess.run([str(toolroot / 'usr/bin/mksquashfs'), str(ROOT), str(image),
                    '-noappend', '-comp', 'gzip', '-processors', '2', '-no-progress', '-wildcards',
                    '-e', 'proc/*', 'sys/*', 'dev/*', 'run/*', 'tmp/*', 'var/tmp/*',
                    'var/log/*', 'var/cache/apt/archives/*.deb'],
                   env=env, stdout=log, stderr=subprocess.STDOUT, check=True)
tool = str(toolroot / 'usr/bin/unsquashfs')


def read(path):
    return subprocess.check_output([tool, '-cat', str(image), path], env=env)


assert read('etc/machine-id') == b''
assert b'F8-PRO' in read('etc/f8-pro-evaluation')
for binary in ['usr/lib/systemd/systemd', 'usr/bin/kwin_wayland', 'usr/bin/sddm']:
    content = read(binary)
    assert content[:6] == b'\x7fELF\x02\x01' and struct.unpack_from('<H', content, 18)[0] == 183
listing = subprocess.check_output([tool, '-ls', str(image)], env=env, text=True).splitlines()
assert not any(line.endswith('/' + name) for line in listing
               for name in ['ssh_host_rsa_key', 'ssh_host_ecdsa_key', 'ssh_host_ed25519_key', 'plasmax11.desktop'])
module_paths = [line for line in listing if '/lib/modules/' in line and line.endswith('.ko')]
assert len(module_paths) == 2279
assert all('/' + RELEASE + '/' in line for line in module_paths)
manifest = json.loads((P / 'analysis/armbian/kernel-build/custom-modules-manifest.json').read_text())
module_checks = []
for name in ['cw2015_battery', 'bq25890_charger', 'panthor']:
    item = next(row for row in manifest if row['path'].endswith('/' + name + '.ko'))
    digest = hashlib.sha256(read('usr/lib/modules/' + RELEASE + '/' + item['path'])).hexdigest()
    assert digest == item['sha256']
    module_checks.append(name)
assert b'ssh-keygen -A' in read('usr/lib/systemd/system/f8-pro-ssh-hostkeys.service')
assert read('usr/share/wayland-sessions/plasma.desktop')
assert read('usr/share/sddm/themes/debian-breeze/Main.qml')
with image.open('rb') as stream:
    digest = hashlib.file_digest(stream, 'sha256').hexdigest()
result = {'scope': 'Offline custom-ABI desktop snapshot only; board DT/FIT, login/GPU/input and first-user flow unvalidated',
          'bytes': image.stat().st_size, 'sha256': digest, 'module_release': RELEASE,
          'module_count': len(module_paths), 'key_module_hashes_verified': module_checks,
          'empty_machine_id': True, 'ssh_host_private_keys_absent': True,
          'native_plasma_x11_entry_hidden': True, 'fstab_has_no_mount_entries': True,
          'candidate_sddm_kwin_configs_active': False, 'bootable_board_image': False}
(P / 'analysis/armbian/userspace/verified-wayland-squashfs.json').write_text(json.dumps(result, indent=2) + '\n')
(out / 'SHA256SUMS').write_text(digest + '  rootfs.squashfs\n')
(out / 'DO-NOT-BOOT.txt').write_text('Development desktop snapshot only. Board integration and hardware tests are incomplete.\n')
print(json.dumps(result, indent=2))
