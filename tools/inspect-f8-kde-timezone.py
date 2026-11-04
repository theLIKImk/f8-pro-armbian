import json,subprocess,os
from pathlib import Path
def run(a):
 try:
  r=subprocess.run(a,capture_output=True,text=True,timeout=12);return dict(exit=r.returncode,stdout=r.stdout,stderr=r.stderr)
 except Exception as e:return {'error':str(e)}
o={'packages':run(['dpkg-query','-W','plasma-desktop','kde-config-systemd','tzdata','qml6-module-org-kde-kirigami','qml6-module-org-kde-kcmutils','qml6-module-org-kde-plasma-workspace']),
'kcm_files':run(['sh','-c',"dpkg -L plasma-desktop | grep -E 'clock|time|zone'; dpkg -L plasma-workspace | grep -E 'timezones|timezone|clock' | head -45"]),
'zonefiles':{},'logs':run(['journalctl','-b','--no-pager','-n','180','_COMM=systemsettings']),
'process':run(['pgrep','-af','systemsettings|kcmshell']),
'bus':run(['timedatectl','show'])}
for name in ['/usr/share/zoneinfo/zone.tab','/usr/share/zoneinfo/zone1970.tab','/usr/share/zoneinfo/iso3166.tab']:
 p=Path(name);o['zonefiles'][name]={'exists':p.exists(),'bytes':p.stat().st_size if p.exists() else None}
print(json.dumps(o))
