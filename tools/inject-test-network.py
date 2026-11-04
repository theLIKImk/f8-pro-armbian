"""Inject a private WPA/WPA2-Personal profile without logging credentials."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import uuid


def render_profile(data):
    ssid, password = data.get('ssid'), data.get('psk')
    if not isinstance(ssid, str) or not isinstance(password, str):
        raise ValueError('ssid and psk must be text fields')
    ssid_bytes = ssid.encode('utf-8')
    if not 1 <= len(ssid_bytes) <= 32 or any(c in ssid for c in '\0\r\n'):
        raise ValueError('Fill in a valid Wi-Fi name (1-32 UTF-8 bytes)')
    if re.fullmatch('[0-9a-fA-F]{64}', password):
        key = password.lower()
    elif 8 <= len(password.encode('utf-8')) <= 63 and not any(c in password for c in '\0\r\n'):
        key = hashlib.pbkdf2_hmac('sha1', password.encode('utf-8'), ssid_bytes, 4096, 32).hex()
    else:
        raise ValueError('Fill in a WPA/WPA2 password (8-63 UTF-8 bytes or a 64-digit hex key)')
    # A byte list handles spaces, semicolons, and Unicode SSIDs unambiguously.
    encoded_ssid = ''.join(str(value) + ';' for value in ssid_bytes)
    return ('[connection]\nid=f8-pro-test-wifi\nuuid=' + str(uuid.uuid4()) +
            '\ntype=wifi\nautoconnect=true\nautoconnect-retries=0\n\n'
            '[wifi]\nmode=infrastructure\nssid=' + encoded_ssid +
            '\ncloned-mac-address=preserve\npowersave=2\n\n'
            '[wifi-security]\nkey-mgmt=wpa-psk\npsk=' + key + '\npsk-flags=0\n\n'
            '[ipv4]\nmethod=auto\n\n[ipv6]\nmethod=auto\n').encode('utf-8')


def inject(root, source):
    root = root.resolve()
    if not str(root).startswith('/var/tmp/f8-pro-') or root.name != 'rootfs-vendor-staging':
        raise ValueError('Only the isolated build candidate is accepted')
    if os.getuid() != 0:
        raise ValueError('Run in the Linux build environment as root')
    # Do not include supplied values in errors, stdout, or build manifests.
    data = json.loads(sys.stdin.read() if str(source) == '-' else source.read_text(encoding='utf-8-sig'))
    payload = render_profile(data)
    check = subprocess.run(['chroot', str(root), '/usr/bin/nmcli', '--offline',
                            'connection', 'modify', 'connection.id', 'f8-pro-test-wifi'],
                           input=payload, capture_output=True)
    if check.returncode:
        raise ValueError('NetworkManager rejected the profile; no credentials were written')
    expected_key = re.search(rb'(?m)^psk=([0-9a-f]{64})$', payload)
    retained_key = re.search(rb'(?m)^psk=([0-9a-f]{64})$', check.stdout)
    if not expected_key or not retained_key or expected_key.group(1) != retained_key.group(1):
        raise ValueError('Offline normalization did not retain the supplied key; no credentials were written')
    directory = root / 'etc/NetworkManager/system-connections'
    if not directory.resolve().is_relative_to(root):
        raise ValueError('Connection directory escapes the candidate')
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / 'f8-pro-test-wifi.nmconnection'
    if path.is_symlink():
        raise ValueError('Refusing a linked profile destination')
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, 'wb') as stream:
        stream.write(check.stdout)
    path.chmod(0o600)
    os.chown(path, 0, 0)
    marker = root / 'var/lib/f8-pro/wifi-provisioned'
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.write_text('WPA/WPA2-Personal profile validated offline; real connection not yet tested.\n')
    marker.chmod(0o600)
    record_path = Path(__file__).resolve().parent.parent / 'analysis/test-rootfs/integration.json'
    record = json.loads(record_path.read_text())
    record['wifi_credentials_injected'] = True
    record['wifi_profile_validated_offline'] = True
    record['wifi_real_connection_tested'] = False
    record_path.write_text(json.dumps(record, indent=2) + '\n')
    print('Private Wi-Fi profile validated and installed with root-only permissions.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root', type=Path)
    parser.add_argument('config', type=Path)
    args = parser.parse_args()
    try:
        inject(args.root, args.config)
    except (ValueError, OSError, json.JSONDecodeError):
        raise SystemExit('Wi-Fi input is missing/invalid or could not be installed; no input values were logged.')
