"""Trust the public host key read from the tablet's physical USB log drive."""
import argparse
import base64
import os
from pathlib import Path
import subprocess

p = argparse.ArgumentParser()
p.add_argument('--key-base64', required=True)
a = p.parse_args()
public_key = base64.b64decode(a.key_base64, validate=True).decode('ascii').strip()
parts = public_key.split()
assert len(parts) in (2, 3) and parts[0] == 'ssh-ed25519', 'Expected ED25519 public host key'
blob = base64.b64decode(parts[1], validate=True)
assert len(blob) == 51 and blob[:19] == b'\x00\x00\x00\x0bssh-ed25519\x00\x00\x00\x20'
subprocess.run(['ssh-keygen', '-lf', '/dev/stdin'], input=public_key+'\n', text=True, check=True)
target = Path('/var/tmp/f8-pro-armbian/desktop-t1-known-hosts')
line = 'f8-desktop-t1 ssh-ed25519 ' + parts[1] + '\n'
if target.exists():
    assert target.read_text() == line, 'Different desktop host identity; inspect before changing trust'
else:
    fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, 'w') as stream:
        stream.write(line)
print('Desktop host key registered from physical log drive.')
