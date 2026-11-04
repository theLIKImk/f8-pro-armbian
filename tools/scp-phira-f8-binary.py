"""Transfer the locally verified F8 binary; credentials are accepted only on stdin."""
import argparse,hashlib,json,os,re,subprocess,sys
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--sha256',required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
assert re.fullmatch('[0-9a-f]{64}',a.sha256)
assert a.source.is_file() and hashlib.sha256(a.source.read_bytes()).hexdigest()==a.sha256
d=json.load(sys.stdin);assert d['username']=='likimk' and re.fullmatch(r'[0-9.]+',d['address'])
password=d.pop('password');assert '\n' not in password
known=Path('/var/tmp/f8-pro-armbian/post-wizard-likimk/known_hosts');assert known.is_file()
dest='/home/likimk/phira-f8-r1.incoming'
env=dict(os.environ,SSHPASS=password)
r=subprocess.run(['sshpass','-e','scp','-o','PubkeyAuthentication=no','-o','PreferredAuthentications=password','-o','NumberOfPasswordPrompts=1','-o','StrictHostKeyChecking=yes','-o','UserKnownHostsFile='+str(known),'-o','ConnectTimeout=8',str(a.source),'likimk@'+d['address']+':'+dest],env=env,capture_output=True,text=True,timeout=240)
env.pop('SSHPASS',None);password=None
o={'exit':r.returncode,'destination':dest,'sha256':a.sha256,'bytes':a.source.stat().st_size,'stderr':r.stderr};a.output.write_text(json.dumps(o,indent=2)+'\n');print(json.dumps(o));raise SystemExit(r.returncode)
