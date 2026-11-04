import subprocess,json
from pathlib import Path
def run(a):
 r=subprocess.run(a,capture_output=True,text=True,timeout=20);return dict(exit=r.returncode,stdout=r.stdout,stderr=r.stderr)
print(json.dumps({'waitsync':run(['chronyc','waitsync','5','0.1','0','2']),'tracking':run(['chronyc','tracking']),'sources':run(['chronyc','-n','sources']),'auth':run(['chronyc','-n','authdata']),'timedate':run(['timedatectl','status']),'service':run(['systemctl','is-enabled','chrony.service']),'target':run(['systemctl','show','f8-desktop.target','--property=Wants'])}))
