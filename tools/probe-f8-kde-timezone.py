import json,os,subprocess
from pathlib import Path
def run(a,timeout=12):
 try:
  r=subprocess.run(a,capture_output=True,text=True,timeout=timeout);return dict(exit=r.returncode,stdout=r.stdout,stderr=r.stderr)
 except Exception as e:return {'error':str(e)}
u=['runuser','-u','likimk','--','env','XDG_RUNTIME_DIR=/run/user/1602','DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1602/bus']
code='''
from PyQt6.QtGui import QGuiApplication
from PyQt6.QtQml import QQmlEngine,QQmlComponent
from PyQt6.QtCore import QUrl,QEventLoop,QTimer
import json
app=QGuiApplication([]);engine=QQmlEngine()
for name in ['i18nd','i18ndc']:
 engine.rootContext().setContextProperty(name,engine.evaluate('(function(){return arguments[arguments.length-1];})'))
c=QQmlComponent(engine,QUrl.fromLocalFile('/usr/lib/aarch64-linux-gnu/qt6/qml/org/kde/plasma/workspace/timezoneselector/TimezoneSelector.qml'))
assert c.isReady(),[x.toString() for x in c.errors()]
o=c.create();assert o is not None,[x.toString() for x in c.errors()]
loop=QEventLoop();QTimer.singleShot(1800,loop.quit);loop.exec()
def value(k):
 v=o.property(k)
 return v.toVariant() if hasattr(v,'toVariant') else v
zones=value('availableTimeZones');mapped=value('availableMapTimeZones');regions=value('regionsModel')
print(json.dumps({'component_ready':True,'timezone_count':len(zones or []),'mapped_count':len(mapped or []),'regions_count':len(regions or []),'errors':[x.toString() for x in c.errors()]}))
assert len(zones or [])>100 and len(mapped or [])>100 and len(regions or [])>5
'''
o={'aptlog':run(['journalctl','-u','f8-kde-timezone-deps.service','-n','18','--no-pager']),'packages':run(['dpkg-query','-W','qml6-module-qtlocation','qml6-module-qtpositioning','timezone-data']),'timezone_json':{'exists':Path('/usr/share/timezonefiles/timezones.json').is_file()},'policy':run(['apt-cache','policy','timezone-data']),'probe':run(u+['env','QT_QPA_PLATFORM=offscreen','python3','-I','-c',code])}
print(json.dumps(o))
