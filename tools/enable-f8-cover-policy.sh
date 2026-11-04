#!/bin/sh
set -eu
python3 -I - <<'PY'
import json,os,subprocess,time
from pathlib import Path
home=Path.home();s=json.loads((home/'.cache/f8-cover/status.json').read_text())
assert os.getuid()==1601 and not s['closed'] and s['events_count']>=2
assert any(e['closed'] for e in s['recent_events']) and any(not e['closed'] for e in s['recent_events'])
assert Path('/sys/devices/platform/f8-cover-haptic/hall_raw').read_text().strip()=='1'
p=subprocess.run(['/usr/local/bin/f8-vibrate','--watchdog-test'],capture_output=True,text=True,timeout=4);assert p.returncode==0,p.stdout+p.stderr
config=home/'.config/f8-cover.json';c=json.loads(config.read_text());c.update(validated=True,screen_enabled=True);config.write_text(json.dumps(c)+'\n')
env={**os.environ,'XDG_RUNTIME_DIR':'/run/user/1601','DBUS_SESSION_BUS_ADDRESS':'unix:path=/run/user/1601/bus'}
subprocess.run(['systemctl','--user','enable','f8-cover-screen.service'],env=env,check=True,timeout=8)
time.sleep(2)
print(json.dumps({'watchdog':json.loads(p.stdout),'status':json.loads((home/'.cache/f8-cover/status.json').read_text()),'user_service_enabled':True},indent=2))
PY
