"""Inspect critical paths inside the generated image, without mounting it."""
import argparse
import json
from pathlib import Path
import re
import subprocess

project = Path(__file__).resolve().parent.parent
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('variant', choices=('pending-wifi', 'wifi-test'))
args = parser.parse_args()
record_path = project / ('analysis/test-rootfs/image-' + args.variant + '.json')
record = json.loads(record_path.read_text())
image = Path('/var/tmp/f8-pro-archlinux-20261027/artifacts') / ('f8-pro-arch-' + args.variant + '.img')


def debug(command):
    result = subprocess.run(['debugfs', '-R', command, str(image)], capture_output=True, text=True, check=True)
    return result.stdout, result.stderr


key, _ = debug('stat /home/alarm/.ssh/authorized_keys')
if not re.search(r'Mode:\s+0600', key) or not re.search(r'User:\s+1000\s+Group:\s+1000', key):
    raise RuntimeError('Image authorized_keys ownership or permissions are wrong')
machine_id, _ = debug('stat /etc/machine-id')
if not re.search(r'Size:\s+0\b', machine_id):
    raise RuntimeError('Image contains an assigned machine-id')
for path in ('/etc/ssh/ssh_host_ed25519_key', '/etc/pacman.d/gnupg/private-keys-v1.d'):
    _, diagnostic = debug('stat ' + path)
    if 'File not found' not in diagnostic:
        raise RuntimeError('An identity secret may be present in the image')
policy, _ = debug('cat /etc/ssh/sshd_config.d/10-f8-pro-test.conf')
for value in ('PasswordAuthentication no', 'PermitRootLogin no', 'PubkeyAuthentication yes'):
    if value not in policy:
        raise RuntimeError('Image SSH policy missing')
module, _ = debug('stat /usr/lib/modules/5.10.160/updates/bcmdhd_pcie.ko')
if 'Type: regular' not in module:
    raise RuntimeError('Board Wi-Fi module missing from image')
unit, _ = debug('cat /usr/lib/systemd/system/f8-pro-bluetooth.service')
if 'dev-ttyS9.device' not in unit:
    raise RuntimeError('Image Bluetooth UART mismatch')
if args.variant == 'pending-wifi':
    _, diagnostic = debug('stat /etc/NetworkManager/system-connections/f8-pro-test-wifi.nmconnection')
    if 'File not found' not in diagnostic:
        raise RuntimeError('A private Wi-Fi profile is present in the unprovisioned variant')
else:
    profile, _ = debug('stat /etc/NetworkManager/system-connections/f8-pro-test-wifi.nmconnection')
    if not re.search(r'Mode:\s+0600', profile) or not re.search(r'User:\s+0\s+Group:\s+0', profile):
        raise RuntimeError('Private network profile permissions incorrect in image')
    # Read private data only into memory; never print or save it in check logs.
    content, _ = debug('cat /etc/NetworkManager/system-connections/f8-pro-test-wifi.nmconnection')
    if not re.search(r'(?m)^psk=[0-9a-f]{64}$', content) or not re.search(r'(?m)^ssid=.+$', content):
        raise RuntimeError('Private network profile lost required connection fields')
    candidate = Path('/var/tmp/f8-pro-archlinux-20261027/rootfs-vendor-staging/etc/NetworkManager/system-connections/f8-pro-test-wifi.nmconnection')
    if content != candidate.read_text():
        raise RuntimeError('Image connection differs from the validated candidate')
    record['private_network_contents_verified_without_logging'] = True
record['critical_image_contents_verified'] = True
record_path.write_text(json.dumps(record, indent=2) + '\n')
export = Path(record['export_directory'])
(export / 'manifest.json').write_text(json.dumps(record, indent=2) + '\n')
print('PASS: image key ownership, fresh host identity, no build signing secret, SSH policy, Wi-Fi module and Bluetooth UART')
