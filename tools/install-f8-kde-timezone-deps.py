import json,subprocess,os
from pathlib import Path
assert os.geteuid()==0
def run(a):
 r=subprocess.run(a,capture_output=True,text=True,timeout=10);return dict(exit=r.returncode,stdout=r.stdout,stderr=r.stderr)
p=Path('/usr/lib/aarch64-linux-gnu/qt6/qml/org/kde/plasma/workspace/timezoneselector/TimezoneSelector.qml')
o={'qml':p.read_text(),'policy':run(['apt-cache','policy','qml6-module-qtlocation','qml6-module-qtpositioning']),'start':run(['systemd-run','--unit=f8-kde-timezone-deps','--collect','--setenv=DEBIAN_FRONTEND=noninteractive','/usr/bin/apt-get','-y','--no-install-recommends','install','qml6-module-qtlocation','qml6-module-qtpositioning'])}
print(json.dumps(o))
