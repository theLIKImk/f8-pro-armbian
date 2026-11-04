"""Upload this public build artifact using the session's existing pinned SSH key."""
import argparse,hashlib,json,os,re,subprocess,sys
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
d=json.load(sys.stdin);name=d['username'];address=d['address'];password=d.pop('password')
assert name=='likimk' and re.fullmatch(r'[0-9.]+',address) and '\n' not in password
assert a.source.name=='Phira-linux-arm64-v0.8.2.tar.gz' and a.source.is_file()
assert hashlib.sha256(a.source.read_bytes()).hexdigest()=='6f710fd40224eb926dbfdbb66894335082b8f4d18980422abc939ebbd0bed240'
known=Path('/var/tmp/f8-pro-armbian/post-wizard-likimk/known_hosts');assert known.is_file()
dest='/home/likimk/Phira-linux-arm64-v0.8.2-7505793.tar.gz'
env=dict(os.environ,SSHPASS=password)
cmd=['sshpass','-e','scp','-o','BatchMode=no','-o','PubkeyAuthentication=no','-o','PreferredAuthentications=password','-o','NumberOfPasswordPrompts=1','-o','StrictHostKeyChecking=yes','-o','UserKnownHostsFile='+str(known),'-o','ConnectTimeout=8',str(a.source),name+'@'+address+':'+dest]
r=subprocess.run(cmd,env=env,capture_output=True,text=True,timeout=240)
env.pop('SSHPASS',None);password=None
record={'exit':r.returncode,'destination':dest,'bytes':a.source.stat().st_size,'stdout':r.stdout,'stderr':r.stderr}
a.output.write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record));raise SystemExit(r.returncode)
