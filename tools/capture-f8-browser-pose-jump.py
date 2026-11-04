import json,subprocess,time
from pathlib import Path
code="""import dbus,json,time,math
from pathlib import Path
bus=dbus.SessionBus();p=dbus.Interface(bus.get_object('net.f8.Sensors','/net/f8/Sensors'),'net.f8.Sensors1');frames=[]
for i in range(160):
 now=time.monotonic()
 try:s=json.loads(str(p.GetSnapshot(timeout=.3)));frames.append({'read':now,**s})
 except Exception as e:frames.append({'read':now,'error':str(e)})
 time.sleep(.1)
print(json.dumps({'frames':frames,'browser':json.loads((Path('/run/user/1602')/'f8-browser-pose.json').read_text())}))
"""
pre=['runuser','-u','likimk','--','env','XDG_RUNTIME_DIR=/run/user/1602','DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1602/bus']
r=subprocess.run(pre+['python3','-c',code],capture_output=True,text=True,timeout=35);print(json.dumps({'exit':r.returncode,'stdout':r.stdout,'stderr':r.stderr}))
