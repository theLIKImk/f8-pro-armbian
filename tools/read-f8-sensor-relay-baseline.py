import json,subprocess,os
from pathlib import Path
def run(a):
 r=subprocess.run(a,capture_output=True,text=True,timeout=12);return {'exit':r.returncode,'out':r.stdout[:10000],'err':r.stderr[:1000]}
o={'packages':run(['dpkg-query','-W','chromium','python3-dbus','python3-gi','python3-pyqt6','libqt6sensors6','iio-sensor-proxy']),'iio':{},'backlight':{},'powerdevil':run(['runuser','-u','likimk','--','env','XDG_RUNTIME_DIR=/run/user/1602','DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1602/bus','busctl','--user','tree','org.kde.Solid.PowerManagement'])}
for p in Path('/sys/bus/iio/devices').glob('iio:device*'):o['iio'][p.name]={'name':(p/'name').read_text().strip(),'files':[x.name for x in p.iterdir()]}
for p in Path('/sys/class/backlight').glob('*'):o['backlight'][str(p)]={n:(p/n).read_text().strip() for n in ['brightness','actual_brightness','max_brightness','bl_power'] if (p/n).exists()}
o['session']=run(['runuser','-u','likimk','--','env','XDG_RUNTIME_DIR=/run/user/1602','DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1602/bus','busctl','--user','introspect','org.kde.Solid.PowerManagement','/org/kde/Solid/PowerManagement/Actions/BrightnessControl'])
print(json.dumps(o))
