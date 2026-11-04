"""Execute a script on native Armbian only after physical host-key registration."""
import argparse
from pathlib import Path
import re
import subprocess
p=argparse.ArgumentParser()
p.add_argument('--address',required=True)
p.add_argument('--script',required=True,type=Path)
p.add_argument('--sudo',action='store_true')
a=p.parse_args()
assert re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9.-]*',a.address)
hosts=Path('/var/tmp/f8-pro-armbian/desktop-t1-known-hosts')
assert hosts.is_file(),'First register SSHKEY.PUB read from the physical USB log drive'
args=['ssh','-T','-i','/var/tmp/f8-pro-archlinux-20261027/private-keys/f8-pro-test-ed25519',
      '-o','BatchMode=yes','-o','IdentitiesOnly=yes','-o','StrictHostKeyChecking=yes',
      '-o','HostKeyAlias=f8-desktop-t1','-o','UserKnownHostsFile='+str(hosts),'-o','ConnectTimeout=8',
      'f8test@'+a.address,'sudo -n sh -s' if a.sudo else 'sh -s']
payload=a.script.read_bytes().replace(b'\r\n',b'\n');assert b'\0' not in payload
raise SystemExit(subprocess.run(args,input=payload,timeout=90).returncode)
