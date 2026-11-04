"""User-session sensor test with bounded local I/O and a short GPU scene."""
import json,os,subprocess,tempfile
from pathlib import Path
from PyQt6.QtCore import QCoreApplication,QMetaType,QTimer
from PyQt6.QtDBus import QDBusArgument,QDBusConnection,QDBusMessage
app=QCoreApplication([]);bus=QDBusConnection.sessionBus()
ids=['gpu/all/usage','gpu/gpu0/usage','gpu/gpu0/coreFrequency','gpu/gpu0/temperature','disk/all/total','disk/all/used','disk/all/free','disk/all/read','disk/all/write']
message=QDBusMessage.createMethodCall('org.kde.ksystemstats1','/org/kde/ksystemstats1','org.kde.ksystemstats1','subscribe')
message.setArguments([QDBusArgument(ids,QMetaType.Type.QStringList.value)])
reply=bus.call(message)
if reply.type()==QDBusMessage.MessageType.ErrorMessage:raise RuntimeError(reply.errorMessage())
out={'samples':[],'subscription':'ok'};child=None;temporary=None;count=0
def sample():
 global count,child,temporary
 count+=1
 r=subprocess.run(['busctl','--user','--json=short','call','org.kde.ksystemstats1','/org/kde/ksystemstats1','org.kde.ksystemstats1','sensorData','as',str(len(ids)),*ids],capture_output=True,text=True,timeout=5)
 if r.returncode==0:
  values=json.loads(r.stdout)['data'][0];out['samples'].append({'second':count,'values':{k:v['data'] for k,v in values}})
 else:out.setdefault('errors',[]).append(r.stderr)
 if count==2:
  f=tempfile.NamedTemporaryFile(prefix='f8-monitor-probe-',dir=Path.home()/'.cache',delete=False);temporary=Path(f.name)
  f.write(b'\0'*(16*1024*1024));f.flush();os.fsync(f.fileno());f.close()
  child=subprocess.Popen(['glmark2-es2-wayland','--off-screen','--frame-end','finish','--size','800x600','-b','build:duration=4'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 if count>=10:
  timer.stop()
  if child and child.poll() is None:child.terminate();child.wait(timeout=3)
  if temporary and temporary.exists():temporary.unlink()
  s=os.statvfs('/');out['root_statvfs']={'total':s.f_blocks*s.f_frsize,'available':s.f_bavail*s.f_frsize}
  print(json.dumps(out));app.quit()
timer=QTimer();timer.timeout.connect(sample);timer.start(1000);app.exec()
