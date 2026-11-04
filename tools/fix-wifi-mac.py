"""Apply the narrowly scoped F8-PRO Wi-Fi MAC workaround without exposing PSK.

Run inside the mounted target chroot before NetworkManager starts. Keeps an
original root-only backup and changes neither SSID nor authentication fields.
"""
import os
from pathlib import Path
import re
import stat

DROPIN = b'''[device-f8-pro-wifi]
match-device=interface-name:wlan0
wifi.scan-rand-mac-address=no

[connection-f8-pro-wifi]
match-device=interface-name:wlan0
wifi.cloned-mac-address=preserve
'''


def patch_profile(payload):
    if not re.search(rb'(?m)^id=f8-pro-test-wifi\r?$', payload):
        raise ValueError('Unexpected profile identity')
    parts = re.split(rb'(?m)^(\[[^\r\n]+\]\r?\n)', payload)
    count = 0
    for i in range(1, len(parts), 2):
        if parts[i].strip() != b'[wifi]':
            continue
        count += 1
        body = parts[i+1]
        matches = re.findall(rb'(?m)^cloned-mac-address=.*$', body)
        if len(matches) != 1:
            raise ValueError('Unexpected Wi-Fi MAC field layout')
        parts[i+1] = re.sub(rb'(?m)^cloned-mac-address=[^\r\n]*', b'cloned-mac-address=preserve', body)
    if count != 1:
        raise ValueError('Unexpected Wi-Fi section count')
    result = b''.join(parts)
    # Credentials are compared only in memory, never printed.
    for field in (b'ssid', b'psk', b'psk-flags', b'key-mgmt', b'uuid'):
        pattern = rb'(?m)^'+field+rb'=[^\r\n]*'
        if re.findall(pattern, payload) != re.findall(pattern, result):
            raise ValueError('A protected field changed')
    return result


def atomic_write(path, payload, mode):
    if path.is_symlink():
        raise ValueError('Linked destination refused')
    temporary = path.with_name(path.name+'.f8tmp')
    fd = os.open(temporary, os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW, mode)
    try:
        with os.fdopen(fd, 'wb') as out:
            out.write(payload)
            out.flush()
            os.fchmod(out.fileno(), mode)
            os.fsync(out.fileno())
        os.replace(temporary, path)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise


def install(root=Path('/')):
    root = root.resolve()
    if os.getuid() != 0 or not (root/'etc/arch-release').is_file():
        raise ValueError('Requires the Arch target as root')
    profile = root/'etc/NetworkManager/system-connections/f8-pro-test-wifi.nmconnection'
    if profile.is_symlink() or not profile.resolve().is_relative_to(root):
        raise ValueError('Unexpected profile path')
    attrs = profile.stat()
    if not stat.S_ISREG(attrs.st_mode) or attrs.st_uid != 0 or attrs.st_mode & 0o777 != 0o600:
        raise ValueError('Profile ownership or mode invalid')
    original = profile.read_bytes()
    changed = patch_profile(original)
    backup = root/'var/lib/f8-pro/network-backup'
    if not backup.resolve().is_relative_to(root) or backup.is_symlink():
        raise ValueError('Unexpected backup directory')
    backup.mkdir(parents=True, exist_ok=True, mode=0o700)
    backup.chmod(0o700)
    saved = backup/'wifi-before-mac-fix.nmconnection'
    if not saved.exists():
        atomic_write(saved, original, 0o600)
    elif saved.is_symlink() or not saved.is_file() or saved.stat().st_mode & 0o777 != 0o600:
        raise ValueError('Existing backup permissions invalid')
    directory = root/'etc/NetworkManager/conf.d'
    if not directory.resolve().is_relative_to(root):
        raise ValueError('Unexpected drop-in directory')
    directory.mkdir(parents=True, exist_ok=True)
    atomic_write(directory/'90-f8-pro-mac-preserve.conf', DROPIN, 0o644)
    if changed != original:
        atomic_write(profile, changed, 0o600)
    print('Wi-Fi MAC workaround installed; credentials preserved; original backup remains private.')


if __name__ == '__main__':
    try:
        install()
    except Exception:
        raise SystemExit('Wi-Fi MAC workaround failed; no credentials were logged.')
