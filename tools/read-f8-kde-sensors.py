import json,os,subprocess
from pathlib import Path
assert os.geteuid()==0 and os.environ.get('SUDO_USER')=='likimk'
u=['runuser','-u','likimk','--','env','XDG_RUNTIME_DIR=/run/user/1602','DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1602/bus']
out={}
for name,args in [('sensors',u+['busctl','--user','--json=short','call','org.kde.ksystemstats1','/org/kde/ksystemstats1','org.kde.ksystemstats1','allSensors']),('udisks',['systemctl','status','udisks2.service','--no-pager']),('dbus_disks',['busctl','--system','tree','org.freedesktop.UDisks2']),('apt_policy',['apt-cache','policy','libksysguard-dev','qt6-base-dev','libkf6coreaddons-dev','libkf6solid-dev'])]:
 try:r=subprocess.run(args,capture_output=True,text=True,timeout=12);out[name]={'exit':r.returncode,'stdout':r.stdout,'stderr':r.stderr}
 except (OSError,subprocess.TimeoutExpired) as e:out[name]={'error':str(e)}
out['pages']={p.name:p.read_text() for p in Path('/home/likimk/.local/share/plasma-systemmonitor').glob('*.page')}
print(json.dumps(out,indent=2))
