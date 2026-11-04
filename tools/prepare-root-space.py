"""Back up current target configuration privately, verify, then grow known root.

Linux/WSL only. The backup contains credentials and is never printed. It is a
configuration/identity backup paired with the preserved base image, not a full
live filesystem snapshot.
"""
import hashlib
from pathlib import Path
import subprocess
import sys
import tarfile

BASE = Path('/var/tmp/f8-pro-archlinux-20261027')
PROJECT = Path(__file__).resolve().parent.parent
SSH = ['ssh', '-T', '-i', str(BASE/'private-keys/f8-pro-test-ed25519'),
       '-o', 'BatchMode=yes', '-o', 'IdentitiesOnly=yes', '-o', 'StrictHostKeyChecking=yes',
       '-o', 'UserKnownHostsFile='+str(BASE/'test-known-hosts'),
       '-o', 'ConnectTimeout=8', 'alarm@192.168.1.227', 'sudo -n sh -s']


def main():
    import os
    if sys.platform != 'linux':
        raise SystemExit('Run in the existing build WSL')
    os.umask(0o077)
    directory = BASE/'backups'
    directory.mkdir(mode=0o700, exist_ok=True)
    backup = directory/'pre-root-grow-20261028-config.tar.gz'
    if backup.exists():
        raise SystemExit('Backup already exists; inspect state before repeating maintenance')
    payload = (PROJECT/'tools/backup-root-config.sh').read_bytes().replace(b'\r\n', b'\n')
    with backup.open('xb') as out:
        subprocess.run(SSH, input=payload, stdout=out, check=True, timeout=180)
    subprocess.run(['gzip', '-t', str(backup)], check=True)
    required = {'etc/machine-id', 'etc/ssh/ssh_host_ed25519_key',
                'etc/NetworkManager/system-connections/f8-pro-test-wifi.nmconnection',
                'home/alarm/.ssh/authorized_keys'}
    with tarfile.open(backup, 'r:gz') as archive:
        entries = archive.getmembers()
        if any(m.name.startswith('/') or '..' in m.name.split('/') for m in entries):
            raise RuntimeError('Unsafe backup path')
        if not required <= {m.name for m in entries if m.isfile()}:
            raise RuntimeError('Backup is missing critical configuration or identity')
    with backup.open('rb') as stream:
        digest = hashlib.file_digest(stream, 'sha256').hexdigest()
    backup.with_suffix(backup.suffix+'.sha256').write_text(digest+'\n')
    print('Private configuration/identity backup verified; no contents logged.', flush=True)
    # Only a fixed-format digest is inserted into the root script, never secrets.
    prefix = ("set -eu\numask 077\nmkdir -p /var/lib/f8-pro/maintenance\n"
              "chmod 0700 /var/lib/f8-pro/maintenance\n"
              "printf '%s\\n' '"+digest+"' >/var/lib/f8-pro/maintenance/config-backup-verified.sha256\n")
    grow = (PROJECT/'tools/grow-verified-rootfs.sh').read_bytes().replace(b'\r\n', b'\n')
    subprocess.run(SSH, input=prefix.encode()+grow, check=True, timeout=900)
    print('PRIVATE_BACKUP='+str(backup), flush=True)


if __name__ == '__main__':
    main()
