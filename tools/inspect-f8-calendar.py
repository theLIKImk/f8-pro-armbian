import subprocess,json,pwd
from pathlib import Path
def run(a):
 r=subprocess.run(a,capture_output=True,text=True,timeout=12);return dict(exit=r.returncode,stdout=r.stdout,stderr=r.stderr)
o={'packages':run(['dpkg-query','-W','kdeplasma-addons','plasma-calendar-addons','libkf6calendarcore6','libicu78']), 'search':run(['apt-cache','search','--names-only','plasma.*calendar|plasma.*addons']), 'clock_files':run(['sh','-c',"dpkg -L plasma-workspace | grep -E 'digitalclock|calendar' | head -65"]),'qml_matches':[],'configs':{}}
base=Path('/usr/share/plasma/plasmoids/org.kde.plasma.digitalclock/contents')
for p in base.rglob('*.qml'):
 s=p.read_text(errors='replace')
 if any(x in s.lower() for x in ['alternatecalendar','calendarplugin','calendarplugins']):o['qml_matches'].append({'path':str(p),'lines':[x for x in s.splitlines() if any(y in x.lower() for y in ['alternate','plugin','calendar'])][:35]})
p=Path('/home/likimk/.config/plasma-org.kde.plasma.desktop-appletsrc')
if p.is_file():
 # Keep only clock settings, not other widget contents.
 import configparser
 c=configparser.ConfigParser(interpolation=None,strict=False);c.optionxform=str;c.read(p)
 groups=[section for section in c.sections() if c[section].get('plugin')=='org.kde.plasma.digitalclock']
 for group in groups:
  for section in c.sections():
   if section==group or section.startswith(group+']['):o['configs'][section]=dict(c[section])
print(json.dumps(o))
