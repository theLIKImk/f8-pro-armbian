import json,pwd,subprocess
u=['runuser','-u','likimk','--','env','XDG_RUNTIME_DIR=/run/user/1602','DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1602/bus']
def run(a):
 r=subprocess.run(a,capture_output=True,text=True,timeout=12);return dict(exit=r.returncode,stdout=r.stdout,stderr=r.stderr)
print(json.dumps({'apt':run(['journalctl','-u','f8-fcitx5-deps.service','-n','20','--no-pager']),'versions':run(['dpkg-query','-W','fcitx5-frontend-qt5','fcitx5-frontend-qt6','fcitx5-frontend-gtk3','fcitx5-frontend-gtk4']),'tablet_mode':run(u+['qdbus6','org.kde.KWin','/org/kde/KWin','org.kde.KWin.TabletModeManager.tabletMode']),'feedback':run(u+['busctl','--user','introspect','org.sigxcpu.Feedback','/org/sigxcpu/Feedback','org.sigxcpu.Feedback.Haptic']),'uinput':run(['modprobe','uinput'])}))
