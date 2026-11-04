"""Reversibly hide the packaged Plasma X11 session in the isolated root."""
import fcntl
from pathlib import Path
import subprocess

B = Path('/var/tmp/f8-pro-armbian')
ROOT = B / 'rootfs-trixie-wayland'
lock = (B / 'wayland-install.lock').open('a')
fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
assert (B / 'wayland-packages-installed.ok').is_file()
path = '/usr/share/xsessions/plasmax11.desktop'
diverted = path + '.f8-disabled'
if (ROOT / path.lstrip('/')).is_file():
    assert not (ROOT / diverted.lstrip('/')).exists()
    subprocess.run(['chroot', str(ROOT), 'dpkg-divert', '--local', '--add', '--rename',
                    '--divert', diverted, path], check=True)
else:
    listing = subprocess.check_output(['chroot', str(ROOT), 'dpkg-divert', '--list', path], text=True)
    assert diverted in listing
assert not (ROOT / path.lstrip('/')).exists()
assert 'startplasma-x11' in (ROOT / diverted.lstrip('/')).read_text()
print('Plasma X11 session diverted only in isolated root; original retained and package updates respect diversion')
