"""Apply a board-specific SensorProxy matrix; preserve raw sensor coordinates."""
import base64,json,subprocess
from pathlib import Path
P=Path(__file__).resolve().parents[1];out=P/'local/hardware/motion-s1'
assert not (out/'orientation-fix01.json').exists()
payload=base64.b64encode((P/'armbian/motion/99-f8-pro-sensor-mount.rules').read_bytes()).decode()
code='''import base64,hashlib,json,subprocess,time
from pathlib import Path
assert Path('/proc/sys/kernel/random/boot_id').read_text().strip()=='62ae5abd-745b-4b3a-85f4-5910371868b0'
assert Path('/sys/firmware/devicetree/base/chosen/f8-motion-trial').read_bytes()==b's1\\0'
devices=[p for p in Path('/sys/bus/iio/devices').glob('iio:device*') if (p/'name').read_text().strip()=='mpu6500']
assert len(devices)==1;device=devices[0]
assert (device/'in_accel_mount_matrix').read_text().strip()=='0, 1, 0; 1, 0, 0; 0, 0, -1'
rule=Path('/etc/udev/rules.d/99-f8-pro-sensor-mount.rules');assert not rule.exists() and not rule.is_symlink()
def run(args,check=True,timeout=12):
 p=subprocess.run(args,capture_output=True,text=True,timeout=timeout)
 d={'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr}
 if check and p.returncode:raise RuntimeError(str(d))
 return d
def properties():return run(['udevadm','info','--query=property','--path='+str(device)])
def reload():
 run(['udevadm','control','--reload-rules'])
 run(['udevadm','trigger','--action=change',str(device)])
 run(['udevadm','settle','--timeout=5'])
 run(['systemctl','restart','iio-sensor-proxy.service'])
before=properties()
stage=Path('/var/lib/f8-pro/motion-orientation01');stage.mkdir(exist_ok=False)
(stage/'before-properties.txt').write_text(before['stdout'])
try:
 rule.write_bytes(base64.b64decode(PAYLOAD));rule.chmod(0o644)
 reload();after=properties()
 assert 'ACCEL_MOUNT_MATRIX=0,-1,0;-1,0,0;0,0,-1' in after['stdout'],after
 active=run(['systemctl','is-active','iio-sensor-proxy','f8-motion','sddm','f8-bluetooth','f8-usb-otg'])
 prefix=['runuser','-u','f8test','--','env','XDG_RUNTIME_DIR=/run/user/1601','DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1601/bus']
 monitor=run(prefix+['timeout','5','monitor-sensor','--accel'],False,8)
 failed=run(['systemctl','--failed','--no-legend','--no-pager']);assert not failed['stdout'].strip(),failed
 result={'success':True,'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
 'before_properties':before,'after_properties':after,'services':active,'monitor':monitor,
 'rule_path':str(rule),'rule_sha256':hashlib.sha256(rule.read_bytes()).hexdigest(),
 'effective_desktop_matrix':'0,-1,0;-1,0,0;0,0,-1','kernel_matrix_unchanged':(device/'in_accel_mount_matrix').read_text().strip(),
 'failed_units':failed,'user_visual_confirmation_pending':True}
except Exception:
 rule.unlink(missing_ok=True);reload();raise
(stage/'result.json').write_text(json.dumps(result,indent=2)+'\\n');print(json.dumps(result,indent=2))
'''.replace('PAYLOAD',repr(payload))
runner=out/'orientation-fix01-runner.sh';assert not runner.exists()
runner.write_text("#!/bin/sh\nset -eu\npython3 -I - <<'PY'\n"+code+'\nPY\n')
r=subprocess.run(['python3',str(P/'tools/ssh-f8-desktop.py'),'--address','192.168.1.227','--script',str(runner),'--sudo'],capture_output=True,text=True,timeout=100)
assert r.returncode==0,r.stderr[-2000:]
d=json.loads(r.stdout);(out/'orientation-fix01.json').write_text(json.dumps(d,indent=2)+'\n')
print(json.dumps({k:d[k] for k in ['success','boot_id','services','monitor','rule_sha256','effective_desktop_matrix','failed_units']},indent=2))
