import subprocess,json
from pathlib import Path
def run(a):
 r=subprocess.run(a,capture_output=True,text=True,timeout=10);return dict(exit=r.returncode,stdout=r.stdout,stderr=r.stderr)
r=run(['apt-cache','search','--names-only','qt6.*(location|geoservices)'])
o={'search':r,'show':run(['apt-cache','show','qml6-module-qtlocation','libqt6location6'])}
names=[line.split(' - ')[0] for line in r['stdout'].splitlines() if ('plugin' in line.split(' - ')[0] and 'dev' not in line.split(' - ')[0])]
assert len(names)==1,names
o['selected']=names[0];o['install']=run(['systemd-run','--unit=f8-kde-timezone-map-deps','--collect','--setenv=DEBIAN_FRONTEND=noninteractive','/usr/bin/apt-get','-y','--no-install-recommends','install',names[0]])
print(json.dumps(o))
