"""Inspect a fully configured desktop root; never starts the compositor/services."""
import configparser
import fcntl
import json
from pathlib import Path
import struct
import subprocess

P = Path(__file__).resolve().parents[1]
B = Path('/var/tmp/f8-pro-armbian')
ROOT = B / 'rootfs-trixie-wayland'
lock = (B / 'wayland-install.lock').open('a')
fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
assert (B / 'wayland-packages-installed.ok').is_file(), 'Package installation not complete'
output = subprocess.check_output([
    'dpkg-query', '--admindir=' + str(ROOT / 'var/lib/dpkg'), '-W',
    '-f=${Package}\t${Architecture}\t${Version}\t${db:Status-Status}\n'], text=True)
packages = {}
for line in output.splitlines():
    name, architecture, version, state = line.split('\t')
    assert state in ['installed', 'config-files', 'not-installed'], (name, state)
    packages[name] = {'architecture': architecture, 'version': version, 'state': state}
required = [line.strip() for line in (P / 'armbian/wayland-packages.txt').read_text().splitlines()
            if line.strip() and not line.lstrip().startswith('#')]
for name in required:
    assert name in packages and packages[name]['state'] == 'installed', ('Missing configured package', name)
assert packages.get('kwin-x11', {}).get('state') != 'installed'
binaries = {}
for name in ['kwin_wayland', 'startplasma-wayland', 'sddm', 'maliit-keyboard']:
    path = ROOT / 'usr/bin' / name
    header = path.read_bytes()[:64]
    assert header[:6] == b'\x7fELF\x02\x01' and struct.unpack_from('<H', header, 18)[0] == 183, name
    binaries[name] = {'architecture': 'AArch64', 'package_runtime_tested': False}
entry = ROOT / 'usr/share/applications/com.github.maliit.keyboard.desktop'
desktop = configparser.ConfigParser(interpolation=None)
desktop.read(entry)
assert desktop['Desktop Entry']['Exec'].split()[0] == 'maliit-keyboard'
sessions = list((ROOT / 'usr/share/wayland-sessions').glob('*.desktop'))
assert any('startplasma-wayland' in path.read_text() for path in sessions)
for path in (ROOT / 'usr/share/xsessions').glob('*.desktop'):
    assert 'startplasma-x11' not in path.read_text(), path
assert (ROOT / 'usr/share/sddm/themes/debian-breeze/Main.qml').is_file()
assert (ROOT / 'usr/lib/aarch64-linux-gnu/qt6/plugins/platforminputcontexts/libqtvirtualkeyboardplugin.so').is_file()
host_keys = [path.name for path in (ROOT / 'etc/ssh').glob('ssh_host_*_key')]
machine_id = (ROOT / 'etc/machine-id').read_text().strip()
modules = sorted(path.name for path in (ROOT / 'usr/lib/modules').iterdir() if path.is_dir())
result = {'scope': 'Offline installed-package/ELF/session check, not a Wayland/GPU/input or login test',
          'required_packages': {name: packages[name] for name in required}, 'binaries': binaries,
          'wayland_sessions': [path.name for path in sessions], 'kwin_x11_installed': False,
          'maliit_desktop_entry_verified': True, 'debian_breeze_theme_present': True,
          'module_releases': modules, 'build_machine_id_nonempty': bool(machine_id),
          'build_ssh_private_key_filenames': host_keys,
          'identity_sanitization_required': bool(machine_id or host_keys),
          'candidate_configs_installed_by_verifier': False, 'bootable_image_ready': False}
report = P / 'analysis/armbian/userspace/verified-wayland-packages.json'
report.write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
