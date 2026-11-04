import subprocess,json
from pathlib import Path
def run(a):
 r=subprocess.run(a,capture_output=True,text=True,timeout=12);return dict(exit=r.returncode,stdout=r.stdout,stderr=r.stderr)
o={'status':run(['journalctl','-u','f8-calendar-deps.service','-n','12','--no-pager']),'files':run(['dpkg','-L','plasma-calendar-addons']),'configs':{}}
base=Path('/usr/lib/aarch64-linux-gnu/qt6/plugins/plasmacalendarplugins')
for p in base.rglob('*'):
 if p.is_file() and p.suffix in ['.qml','.xml','.kcfg','.json']:o['configs'][str(p)]=p.read_text(errors='replace')[:15000]
p=Path('/home/likimk/.config/plasma_calendar_alternatecalendar');o['alternate_config']=p.read_text() if p.is_file() else None
print(json.dumps(o))
