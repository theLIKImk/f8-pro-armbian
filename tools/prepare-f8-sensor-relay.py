from pathlib import Path
import base64,json,hashlib,py_compile
P=Path(__file__).resolve().parents[1];A=P/'armbian/sensor-relay';O=P/'outputs/armbian/f8-sensor-relay-r2';K=P/'outputs/armbian/f8-sensor-relay-r1';R=O/'rootfs';R.mkdir(parents=True,exist_ok=True)
files={}
def add(source,target,mode=0o644):
 b=source.read_bytes().removeprefix(b'\xef\xbb\xbf');b=b if source.suffix=='.ko' else b.replace(b'\r\n',b'\n');p=R/target;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
 if source.suffix=='.py':compile(b,str(source),'exec')
 files[target]={'data':base64.b64encode(b).decode(),'mode':mode,'sha256':hashlib.sha256(b).hexdigest()}
for n in ['motion_examples_math.py','gyro_stabilizer.py','sensor_fusion.py','sensor_examples.py','fusion_view.py']:
 add(P/'armbian/motion'/n,'usr/local/lib/f8-pro/'+n,0o755)
for n in ['browser_pose_math.py','browser_pose_bridge.py','relay_reading.py','brightness_policy.py','sensor-relay.py','sensor-relay-panel.py']:add(A/n,'usr/local/lib/f8-pro/'+n,0o755)
add(P/'armbian/camera/chromium-camera-launch.py','usr/local/bin/f8-chromium-camera',0o755)
add(A/'codertools-motion-fix.js','usr/local/lib/f8-pro/codertools-motion-fix.js')
add(A/'sensor-relay-start.py','usr/libexec/f8-pro/sensor-relay-start.py')
add(A/'f8-sensor-relay-hardware.service','etc/systemd/system/f8-sensor-relay-hardware.service')
add(A/'f8-sensor-relay.service','etc/systemd/user/f8-sensor-relay.service')
for n in ['72-f8-sensor-relay.rules','99-f8-sensor-relay.rules']:add(A/n,'etc/udev/rules.d/'+n)
add(A/'f8-sensor-relay','usr/local/bin/f8-sensor-relay',0o755)
add(A/'f8-sensor-relay.desktop','usr/share/applications/f8-sensor-relay.desktop')
add(A/'f8-sensor-relay-autostart.desktop','etc/xdg/autostart/f8-sensor-relay-autostart.desktop')
add(K/'f8_sensor_relay.ko','usr/lib/modules/6.1.115-vendor-rk35xx/extra/f8-pro/f8_sensor_relay.ko')
add(K/'module-check.json','usr/share/f8-pro/sensor-relay-r1/module-check.json')
manifest={'files':{k:{'sha256':v['sha256'],'mode':v['mode']} for k,v in files.items()},'personal_calibration_packaged':False,'native_iio_channels':['acceleration','angular velocity','calibrated magnetic field'],'dbus':'session net.f8.Sensors /net/f8/Sensors net.f8.Sensors1','boot_changed':False}
(O/'installation-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
script='''import base64,json,hashlib,os,subprocess,time,pwd
from pathlib import Path
files=PAYLOAD
backup=Path('/var/lib/f8-pro/backups/sensor-relay-r1');backup.mkdir(parents=True,exist_ok=True)
for name,v in files.items():
 p=Path('/')/name;p.parent.mkdir(parents=True,exist_ok=True);b=base64.b64decode(v['data']);assert hashlib.sha256(b).hexdigest()==v['sha256']
 if p.exists() and not (backup/name).exists():
  old=backup/name;old.parent.mkdir(parents=True,exist_ok=True);old.write_bytes(p.read_bytes());old.chmod(p.stat().st_mode&0o777)
 p.write_bytes(b);p.chmod(v['mode'])
def run(a,check=True):
 r=subprocess.run(a,capture_output=True,text=True,timeout=15)
 if check:assert r.returncode==0,(a,r.stdout,r.stderr)
 return {'exit':r.returncode,'out':r.stdout[:3000],'err':r.stderr[:1000]}
run(['depmod','-a']);run(['systemctl','daemon-reload']);run(['udevadm','control','--reload-rules']);hardware=run(['systemctl','enable','--now','f8-sensor-relay-hardware.service'])
run(['udevadm','trigger','--action=add','--subsystem-match=misc','--sysname-match=f8-sensor-feed']);run(['udevadm','trigger','--action=add','--subsystem-match=iio']);run(['udevadm','settle'])
pre=['runuser','-u','likimk','--','env','XDG_RUNTIME_DIR=/run/user/1602','DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1602/bus']
run(pre+['systemctl','--user','daemon-reload']);run(pre+['systemctl','--user','enable','f8-sensor-relay.service']);run(pre+['systemctl','--user','restart','f8-sensor-relay.service']);time.sleep(4)
print(json.dumps({'hardware':hardware,'user_service':run(pre+['systemctl','--user','is-active','f8-sensor-relay.service'],False),'snapshot':json.loads(Path('/run/user/1602/f8-sensor-relay.json').read_text()) if Path('/run/user/1602/f8-sensor-relay.json').exists() else None,'feed_acl':run(['getfacl','-p','/dev/f8-sensor-feed'],False),'journal':run(pre+['journalctl','--user','-u','f8-sensor-relay.service','-n','15','--no-pager'],False)}))
'''.replace('PAYLOAD',repr(files))
(P/'tools/install-f8-sensor-relay-remote.py').write_text(script,encoding='utf-8');print(json.dumps({'files':len(files),'remote_prepared':True}))
