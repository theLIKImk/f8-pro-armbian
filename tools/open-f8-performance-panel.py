import json,os,subprocess
assert os.geteuid()==0 and os.environ.get('SUDO_USER')=='likimk'
p=subprocess.run(['pgrep','-u','1602','-f','/usr/local/lib/f8-pro/performance-panel.py'],capture_output=True,text=True)
if p.returncode==0:print(json.dumps({'already_running':True,'pids':p.stdout.split()}))
else:
 u=['runuser','-u','likimk','--','env','XDG_RUNTIME_DIR=/run/user/1602','DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1602/bus','WAYLAND_DISPLAY=wayland-0','QT_QPA_PLATFORM=wayland']
 r=subprocess.run(u+['systemd-run','--user','--collect','--unit=f8-performance-panel','/usr/bin/python3','/usr/local/lib/f8-pro/performance-panel.py'],capture_output=True,text=True,timeout=10)
 print(json.dumps({'exit':r.returncode,'message':r.stderr}))
