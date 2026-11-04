"""Use preserved tablet host identity for G6 even if DHCP changes its IP."""
import argparse
from pathlib import Path
import re
import subprocess
parser=argparse.ArgumentParser();parser.add_argument('--address',required=True)
parser.add_argument('--script',required=True,type=Path);parser.add_argument('--sudo',action='store_true')
parser.add_argument('--timeout',type=int,default=60)
args=parser.parse_args()
if not 10<=args.timeout<=600:raise SystemExit('Timeout out of range')
if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9.-]*',args.address):raise SystemExit('Invalid address')
base=Path('/var/tmp/f8-pro-archlinux-20261027')
command=['ssh','-T','-i',str(base/'private-keys/f8-pro-test-ed25519'),'-o','BatchMode=yes',
 '-o','IdentitiesOnly=yes','-o','StrictHostKeyChecking=yes','-o','HostKeyAlias=192.168.1.227',
 '-o','UserKnownHostsFile='+str(base/'test-known-hosts'),'-o','ConnectTimeout=8',
 'f8test@'+args.address,'sudo -n sh -s' if args.sudo else 'sh -s']
payload=args.script.read_bytes().replace(b'\r\n',b'\n')
assert b'\0' not in payload
raise SystemExit(subprocess.run(command,input=payload,timeout=args.timeout).returncode)
