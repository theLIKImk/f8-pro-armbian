import os,json,subprocess,time
from pathlib import Path
assert os.geteuid()==0 and os.environ.get('SUDO_USER')=='likimk'
def run(a):
 r=subprocess.run(a,capture_output=True,text=True,timeout=10);return dict(exit=r.returncode,stdout=r.stdout,stderr=r.stderr)
o={'unit':run(['systemctl','cat','chrony.service']),'sources':{}}
for p in Path('/etc/chrony/sources.d').glob('*'):
 if p.is_file():o['sources'][str(p)]=p.read_text()
p=Path('/etc/systemd/system/f8-desktop.target');original=p.read_text()
backup=Path('/var/lib/f8-pro/backups/time-sync-before-r1');backup.mkdir(parents=True,exist_ok=True,mode=0o700)
b=backup/'f8-desktop.target'
if not b.exists():b.write_text(original)
p.write_text(original.replace('systemd-timesyncd.service','chrony.service'))
link=Path('/etc/systemd/system/f8-desktop.target.wants/chrony.service');link.parent.mkdir(exist_ok=True)
if not link.exists() and not link.is_symlink():link.symlink_to('/usr/lib/systemd/system/chrony.service')
for args in [['systemctl','daemon-reload'],['systemctl','enable','--now','chrony.service'],['timedatectl','set-ntp','true']]:
 r=run(args);o[' '.join(args)]=r;assert r['exit']==0,r
run(['chronyc','online']);run(['chronyc','burst','4/4'])
time.sleep(5)
o['tracking']=run(['chronyc','tracking']);o['sources_status']=run(['chronyc','-n','sources','-v']);o['timedate']=run(['timedatectl','status']);o['journal']=run(['journalctl','-u','chrony.service','-n','25','--no-pager'])
print(json.dumps(o))
