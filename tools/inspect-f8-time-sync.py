import subprocess,json,os
from pathlib import Path
assert os.geteuid()==0

def run(a):
 try:
  r=subprocess.run(a,capture_output=True,text=True,timeout=8);return dict(exit=r.returncode,stdout=r.stdout,stderr=r.stderr)
 except Exception as e:return {'error':str(e)}
o={
 'date':run(['date','--iso-8601=ns']),
 'timedate':run(['timedatectl','status']),
 'time_properties':run(['timedatectl','show']),
 'packages':run(['dpkg-query','-W','systemd-timesyncd','chrony','ntpsec']),
 'services':run(['systemctl','status','systemd-timesyncd.service','chrony.service','--no-pager']),
 'target':run(['systemctl','get-default']),
 'desktop_target':run(['systemctl','cat','f8-desktop.target']),
 'journal':run(['journalctl','-u','systemd-timesyncd.service','-u','chrony.service','-n','45','--no-pager']),
 'sync_status':run(['timedatectl','timesync-status']),
 'routes':run(['ip','route','show','default']),
 'dns':run(['getent','ahostsv4','ntp.ubuntu.com']),
 'configs':{}}
for name in ['/etc/timezone','/etc/systemd/timesyncd.conf','/etc/chrony/chrony.conf']:
 p=Path(name)
 if p.is_file():o['configs'][name]=p.read_text()
for base in ['/etc/systemd/timesyncd.conf.d','/usr/lib/systemd/ntp-units.d']:
 for p in Path(base).glob('*'):
  if p.is_file():o['configs'][str(p)]=p.read_text()
print(json.dumps(o))
