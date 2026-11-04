from pathlib import Path
import subprocess,json,base64,time
p=Path('/tmp/f8-browser-pose-live-user.py');p.write_bytes(base64.b64decode('aW1wb3J0IHN5cyxvcyxqc29uLHRpbWUKZnJvbSBwYXRobGliIGltcG9ydCBQYXRoCnN5cy5wYXRoLmluc2VydCgwLCcvdXNyL2xvY2FsL2xpYi9mOC1wcm8nKQpmcm9tIGJyb3dzZXJfcG9zZV9icmlkZ2UgaW1wb3J0IGxhdW5jaApmb2xkZXI9UGF0aC5ob21lKCkvJy5jYWNoZS9mOC1icm93c2VyLXBvc2UtdGVzdCc7Zm9sZGVyLm1rZGlyKHBhcmVudHM9VHJ1ZSxleGlzdF9vaz1UcnVlKQplbnY9ZGljdChvcy5lbnZpcm9uKTtjYW1lcmE9UGF0aCgnL3Vzci9sb2NhbC9saWIvZjgtcHJvL2xpYmY4LWNhbWVyYS1yZWxheS12aWV3LnNvJykKaWYgY2FtZXJhLmV4aXN0cygpOmVudlsnTERfUFJFTE9BRCddPXN0cihjYW1lcmEpCmFyZ3M9WycvdXNyL2Jpbi9jaHJvbWl1bScsJy0tbm8tZmlyc3QtcnVuJywnLS1uby1kZWZhdWx0LWJyb3dzZXItY2hlY2snLCctLW96b25lLXBsYXRmb3JtPXdheWxhbmQnLCctLWVuYWJsZS1mZWF0dXJlcz1HZW5lcmljU2Vuc29yRXh0cmFDbGFzc2VzJywnLS1lbmFibGUtYmxpbmstZmVhdHVyZXM9U2Vuc29yRXh0cmFDbGFzc2VzJywnLS11c2VyLWRhdGEtZGlyPScrc3RyKGZvbGRlci8ncHJvZmlsZScpLCdodHRwczovL3d3dy5jb2RlcnRvb2xzLm5ldC90b29scy9tb3Rpb24tc2Vuc29yLXRlc3QucGhwP2xhbmc9emgnXQp3aXRoIChmb2xkZXIvJ2Jyb3dzZXIubG9nJykub3BlbignYScpIGFzIGxvZzpyYWlzZSBTeXN0ZW1FeGl0KGxhdW5jaChhcmdzLGVudixsb2cpKQo='));p.chmod(0o644)
pre=['runuser','-u','likimk','--','env','XDG_RUNTIME_DIR=/run/user/1602','DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1602/bus']
config=Path('/home/likimk/.config/f8-pro/sensor-relay.json');before=json.loads(config.read_text())
# The user requested live relay testing; ensure the compatibility output is on.
subprocess.run(pre+['gdbus','call','--session','--dest','net.f8.Sensors','--object-path','/net/f8/Sensors','--method','net.f8.Sensors1.SetRelayEnabled','true'],check=True,capture_output=True)
envout=subprocess.check_output(pre+['systemctl','--user','show-environment'],text=True);session={}
for line in envout.splitlines():
 if '=' in line:
  k,v=line.split('=',1)
  if k in ['DISPLAY','WAYLAND_DISPLAY','XAUTHORITY','LANG']:session[k]=v
r=subprocess.run(pre+['systemd-run','--user','--collect','--unit=f8-browser-pose-r2-live']+['--setenv='+k+'='+v for k,v in session.items()]+['/usr/bin/python3',str(p)],capture_output=True,text=True,timeout=10)
time.sleep(3)
print(json.dumps({'launch_exit':r.returncode,'launch_message':r.stderr,'before_relay_enabled':before['relay_enabled'],'status':json.loads(Path('/run/user/1602/f8-browser-pose.json').read_text()),'service':subprocess.run(pre+['systemctl','--user','is-active','f8-browser-pose-r2-live.service'],capture_output=True,text=True).stdout.strip()}))
