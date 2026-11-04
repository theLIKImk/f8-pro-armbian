#!/bin/sh
set -eu
python3 -I - <<'PY'
import json,os,pwd,subprocess
from pathlib import Path
def run(args):
 p=subprocess.run(args,capture_output=True,text=True,timeout=15)
 assert p.returncode==0,(args,p.stdout,p.stderr)
 return p.stdout
state=run(['systemctl','show','f8-camera-app-install','-p','ActiveState','-p','SubState','-p','ExecMainStatus'])
assert 'ActiveState=active' in state and 'SubState=exited' in state and 'ExecMainStatus=0' in state,state
packages=run(['dpkg-query','-W','qv4l2','gstreamer1.0-tools'])
assert Path('/usr/bin/qv4l2').exists()
prefix=['runuser','-u','f8test','--','env','XDG_RUNTIME_DIR=/run/user/1601','DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1601/bus']
desktop=Path(run(prefix+['xdg-user-dir','DESKTOP']).strip());account=pwd.getpwnam('f8test')
assert desktop.is_relative_to(Path(account.pw_dir)) and desktop!=Path(account.pw_dir)
shortcut=desktop/'f8-camera-test.desktop';assert not shortcut.exists()
shortcut.write_text('[Desktop Entry]\nType=Application\nName=Camera Test\nName[zh_CN]=相机测试\nExec=/usr/bin/qv4l2\nIcon=camera-photo\nTerminal=false\nCategories=AudioVideo;Video;\n')
shortcut.chmod(0o755);os.chown(shortcut,account.pw_uid,account.pw_gid)
run(['desktop-file-validate',str(shortcut)])
sockets=[p.name for p in Path('/run/user/1601').glob('wayland-*') if p.is_socket()];assert sockets
run(prefix+['systemd-run','--user','--collect','--unit=f8-camera-test','--setenv=QT_QPA_PLATFORM=wayland','--setenv=WAYLAND_DISPLAY='+sockets[0],'/usr/bin/qv4l2'])
print(json.dumps({'packages':packages,'shortcut':str(shortcut),'launch_requested':True,'capture_started':False,'install_state':state},indent=2))
PY
