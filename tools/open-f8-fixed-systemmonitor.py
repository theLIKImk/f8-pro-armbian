import json,os,signal,subprocess,time
assert os.geteuid()==0 and os.environ.get('SUDO_USER')=='likimk'
r=subprocess.run(['pgrep','-u','1602','-f','^/usr/bin/plasma-systemmonitor( |$)'],capture_output=True,text=True)
for pid in r.stdout.split():
 try:os.kill(int(pid),signal.SIGTERM)
 except ProcessLookupError:pass
time.sleep(1)
u=['runuser','-u','likimk','--','env','XDG_RUNTIME_DIR=/run/user/1602','DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1602/bus','WAYLAND_DISPLAY=wayland-0','QT_QPA_PLATFORM=wayland']
r=subprocess.run(u+['systemd-run','--user','--collect','--unit=f8-systemmonitor-check','/usr/bin/plasma-systemmonitor'],capture_output=True,text=True,timeout=10)
print(json.dumps({'exit':r.returncode,'message':r.stderr}))
