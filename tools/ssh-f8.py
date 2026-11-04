"""Linux-side SSH script runner; avoids Windows shell interpolation of payloads."""
import argparse
from pathlib import Path
import re
import subprocess
import sys

BASE = Path('/var/tmp/f8-pro-archlinux-20261027')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--address', default='192.168.1.227')
    parser.add_argument('--script', required=True, type=Path)
    parser.add_argument('--sudo', action='store_true')
    parser.add_argument('--timeout', type=int, default=300)
    args = parser.parse_args()
    if not 10 <= args.timeout <= 3600:
        parser.error('--timeout must be between 10 and 3600 seconds')
    if sys.platform != 'linux' or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9.-]*', args.address):
        raise SystemExit('Run in the build WSL with a plain host/IP address')
    payload = args.script.read_bytes().replace(b'\r\n', b'\n')
    if b'\0' in payload:
        raise SystemExit('Refusing a non-text script')
    argv = ['ssh', '-T', '-i', str(BASE/'private-keys/f8-pro-test-ed25519'),
            '-o', 'BatchMode=yes', '-o', 'IdentitiesOnly=yes',
            '-o', 'StrictHostKeyChecking=yes',
            '-o', 'UserKnownHostsFile='+str(BASE/'test-known-hosts'),
            '-o', 'ConnectTimeout=8', 'alarm@'+args.address,
            'sudo -n sh -s' if args.sudo else 'sh -s']
    result = subprocess.run(argv, input=payload, timeout=args.timeout)
    return result.returncode


if __name__ == '__main__':
    raise SystemExit(main())
