"""Post-wizard SSH via stdin-only test credentials; never log or store password."""
from pathlib import Path
import argparse,json,os,re,subprocess,sys
p=argparse.ArgumentParser();p.add_argument('--script',required=True,type=Path);p.add_argument('--output',required=True,type=Path);a=p.parse_args()
data=json.load(sys.stdin);address=data['address'];name=data['username'];password=data.pop('password')
assert re.fullmatch(r'[a-z][a-z0-9_-]{0,30}',name)
assert re.fullmatch(r'[0-9.]+',address)
assert '\n' not in password
base=Path('/var/tmp/f8-pro-armbian/post-wizard-'+name);base.mkdir(mode=0o700,exist_ok=True)
known=base/'known_hosts'
# New installation, explicitly supplied LAN address: isolated first-use key record.
# Existing old-system known_hosts is never changed; subsequent key changes fail.
if not known.exists():
 scan=subprocess.run(['ssh-keyscan','-T','5','-t','ed25519',address],capture_output=True,text=True,timeout=8)
 lines=[x for x in scan.stdout.splitlines() if x.startswith(address+' ') and ' ssh-ed25519 ' in x]
 assert len(lines)==1,'SSH service not reachable; enable it locally first'
 known.write_text(lines[0]+'\n');known.chmod(0o600)
fingerprint=subprocess.check_output(['ssh-keygen','-lf',str(known)],text=True).strip()
env=dict(os.environ,SSHPASS=password)
args=['sshpass','-e','ssh','-T','-o','BatchMode=no','-o','PubkeyAuthentication=no','-o','PreferredAuthentications=password','-o','NumberOfPasswordPrompts=1','-o','StrictHostKeyChecking=yes','-o','UserKnownHostsFile='+str(known),'-o','ConnectTimeout=8',name+'@'+address,'sudo -S -p \'\' /usr/bin/python3 -I -']
result=subprocess.run(args,input=password.encode()+b'\n'+a.script.read_bytes(),capture_output=True,env=env,timeout=75)
env.pop('SSHPASS',None);password=None
record={'exit':result.returncode,'host_key':fingerprint,'trust':'isolated first-use record for user-supplied reinstalled LAN host','stdout':result.stdout.decode(errors='replace'),'stderr':result.stderr.decode(errors='replace')}
a.output.write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record,indent=2))
raise SystemExit(result.returncode)
