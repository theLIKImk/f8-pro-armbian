import json,os,subprocess
assert os.geteuid()==0 and os.environ.get('SUDO_USER')=='likimk'
u=['runuser','-u','likimk','--','env','XDG_RUNTIME_DIR=/run/user/1602','DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1602/bus']
ids=['gpu/all/usage','gpu/gpu0/usage','gpu/gpu0/coreFrequency','gpu/gpu0/temperature','disk/all/total','disk/all/used','disk/all/free','disk/all/read','disk/all/write','disk/69056675-4a48-4006-a3f3-5132c00cc6f2/used']
r=subprocess.run(u+['busctl','--user','--json=short','call','org.kde.ksystemstats1','/org/kde/ksystemstats1','org.kde.ksystemstats1','sensorData','as',str(len(ids)),*ids],capture_output=True,text=True,timeout=12)
q=subprocess.run(u+['/usr/bin/python3','-c','from PyQt6.QtDBus import QDBusArgument,QDBusMessage,QDBusConnection; print("QtDBus available")'],capture_output=True,text=True,timeout=8)
print(json.dumps({'exit':r.returncode,'stdout':r.stdout,'stderr':r.stderr,'pyqt_dbus':q.stdout+q.stderr}))
