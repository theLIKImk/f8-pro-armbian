#!/bin/sh
set -eu
python3 -I - <<'PY'
import json,os,subprocess,time
from pathlib import Path
runtime=Path('/run/user/1601');assert os.getuid()==1601
state=json.loads((runtime/'f8-camera-preview-status.json').read_text())
assert not state['engine_pid'] and not state['capture_pid']
assert state['state']=='closed','Preserve existing camera window'
p=subprocess.run(['fuser','/dev/video42','/dev/video22','/dev/video31'],capture_output=True,text=True);assert not p.stdout.strip()
env={**os.environ,'XDG_RUNTIME_DIR':str(runtime),'DBUS_SESSION_BUS_ADDRESS':'unix:path=/run/user/1601/bus'}
sockets=[p.name for p in runtime.glob('wayland-*') if p.is_socket()];assert sockets
common=['systemd-run','--user','--collect','--setenv=WAYLAND_DISPLAY='+sockets[0]]
p=subprocess.run([*common,'--setenv=QT_QPA_PLATFORM=wayland','--unit=f8-codertools-source01','/usr/local/bin/f8-camera-preview','--camera',state.get('camera','back'),'--autostart','--relay'],env=env,capture_output=True,text=True,timeout=10);assert p.returncode==0,p.stderr
for _ in range(100):
 try:state=json.loads((runtime/'f8-camera-preview-status.json').read_text())
 except ValueError:time.sleep(.1);continue
 if state.get('relay_running') and state.get('frames',0)>=14:break
 time.sleep(.1)
assert state.get('relay_running') and state.get('frames',0)>=14,state
url='https://www.codertools.net/tools/webcam-test.php?lang=zh'
p=subprocess.run([*common,'--unit=f8-codertools-browser01','/usr/local/bin/f8-chromium-camera',url],env=env,capture_output=True,text=True,timeout=10);assert p.returncode==0,p.stderr
time.sleep(3)
print(json.dumps({'url':url,'entry':'f8-chromium-camera','normal_permission_prompt':True,'source_state':json.loads((runtime/'f8-camera-preview-status.json').read_text())},indent=2))
PY
