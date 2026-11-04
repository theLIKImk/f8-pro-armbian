import json,os,pwd,subprocess
from pathlib import Path
assert os.geteuid()==0
assert Path('/etc/f8-pro-release-r1').is_file()
out={'sudo_user':os.environ.get('SUDO_USER'),'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'users':[{'name':p.pw_name,'uid':p.pw_uid,'shell':p.pw_shell} for p in pwd.getpwall() if p.pw_uid>=1000 and p.pw_uid<65534]}
for key,args in {'root':['findmnt','-n','-o','SOURCE,FSTYPE','--target','/'],'space':['df','-B1','/'],'sessions':['loginctl','list-sessions','--no-legend','--no-pager']}.items():
 r=subprocess.run(args,capture_output=True,text=True,timeout=10);out[key]={'exit':r.returncode,'stdout':r.stdout}
for name in ['/var/lib/f8-pro/first-run/complete.json','/var/lib/f8-pro/root-grow-r1a/complete.json']:
 p=Path(name);out[name]=json.loads(p.read_text()) if p.exists() else None
out['netplan_profiles']=sum(1 for p in Path('/etc/netplan').glob('*.yaml') if 'access-points:' in p.read_text())
print(json.dumps(out,indent=2))
