import json,subprocess,os,re
from pathlib import Path
def run(a):
 r=subprocess.run(a,capture_output=True,text=True,timeout=10);return dict(exit=r.returncode,stdout=r.stdout,stderr=r.stderr)
o={'kernel':os.uname().release,'iio':[],'i2c':[],'dt':{},'input_devices':run(['cat','/proc/bus/input/devices']),'services':run(['systemctl','is-active','f8-motion.service','f8-compass.service','iio-sensor-proxy.service','f8-cover-screen.service']),'proxy':run(['busctl','--system','get-property','net.hadess.SensorProxy','/net/hadess/SensorProxy','net.hadess.SensorProxy','HasAccelerometer','AccelerometerOrientation','HasAmbientLight','HasProximity','HasCompass']),'installed_fusion':run(['dpkg-query','-W','iio-sensor-proxy','sensorfw','iio-sensor-proxy-qt','libsensorfw-qt6-plugins'])}
for p in Path('/sys/bus/iio/devices').glob('iio:device*'):
 d={'path':str(p),'attributes':{},'driver':str((p/'device/driver').resolve()) if (p/'device/driver').exists() else None}
 for a in p.iterdir():
  if a.is_file() and (a.name in ['name','sampling_frequency','sampling_frequency_available','mount_matrix','in_mount_matrix','in_accel_mount_matrix','in_anglvel_mount_matrix','in_magn_mount_matrix'] or re.fullmatch(r'in_(accel|anglvel|magn|temp).*_(raw|scale|offset)',a.name)):
   try:d['attributes'][a.name]=a.read_text().strip()
   except OSError as e:d['attributes'][a.name]={'error':str(e)}
 for name in ['buffer/enable','trigger/current_trigger']:
  a=p/name
  if a.is_file():d['attributes'][name]=a.read_text().strip()
 o['iio'].append(d)
for p in Path('/sys/bus/i2c/devices').glob('*-*'):
 if (p/'name').is_file():o['i2c'].append({'device':p.name,'name':(p/'name').read_text().strip(),'driver':(p/'driver').resolve().name if (p/'driver').exists() else None})
base=Path('/sys/firmware/devicetree/base')
for p in base.rglob('*'):
 if p.is_dir() and re.search(r'mpu|gyro|compass|ak896|light@|proximity|hall|pressure|acceler',p.name,re.I):
  o['dt'][str(p.relative_to(base))]={f.name:f.read_bytes().hex() for f in p.iterdir() if f.is_file() and f.name in ['compatible','reg','status','layout','poll_delay_ms','interrupts','mount-matrix']}
print(json.dumps(o))
