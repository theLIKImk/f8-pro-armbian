"""RAM-only 122 trial without opening a test app or starting capture."""
import hashlib,json,os,pwd,subprocess,time
from pathlib import Path
assert os.geteuid()==0 and os.environ.get('SUDO_USER')=='likimk'
assert os.uname().release=='6.1.115-vendor-rk35xx'
old=Path('/usr/libexec/f8-pro/f8_gsl_shuping.ko')
assert hashlib.sha256(old.read_bytes()).hexdigest()=='bb8fd9db0bf16972e6760ca9d8ba8489e91a516c31269fc770346fe75d7a505d'
base=subprocess.check_output(['modinfo','-F','srcversion',str(old)],text=True).strip()
assert Path('/sys/module/f8_gsl_shuping/srcversion').read_text().strip()==base
candidate=Path('/var/lib/f8-pro/touch-rate/p122-load2/f8_gsl_shuping.ko')
assert hashlib.sha256(candidate.read_bytes()).hexdigest()=='bb7b4a71e3375ac40045040bcb3b5383972c7402b0ee9bafa41157ccd72355e9'
assert not [l for l in Path('/sys/kernel/tracing/kprobe_events').read_text().splitlines() if 'f8_gsl_shuping:' in l]
uid=pwd.getpwnam('likimk').pw_uid
u=['runuser','-u','likimk','--','env',f'XDG_RUNTIME_DIR=/run/user/{uid}',f'DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/{uid}/bus']
subprocess.run(u+['systemctl','--user','stop','f8-touch-rate-panel.service'],capture_output=True,timeout=8)
W=Path('/var/lib/f8-pro/touch-rate/p122-manual1');assert not W.exists();W.mkdir();W.chmod(0o700)
code=Path('/var/lib/f8-pro/touch-rate/p122-load2/restore.py').read_text()
assert 'B769C22C37A1C4330D85F05' in code
code=code.replace('/p122-load2/restore-result.json','/p122-manual1/restore-result.json')
restore=W/'restore.py';restore.write_text(code);restore.chmod(0o700)
timer='f8-touch-rate-rollback-p122-manual1'
r=subprocess.run(['systemd-run','--unit='+timer,'--on-active=180s','--timer-property=AccuracySec=1s','--property=RuntimeMaxSec=45','/usr/bin/python3',str(restore)],capture_output=True,text=True,timeout=10);assert r.returncode==0,r.stderr
out={'trial':'p122-manual1','test_application_started':False,'capture_started':False,'rollback_seconds':180,'timer':timer+'.timer','boot_asset_changed':False}
try:
 subprocess.run(['rmmod','f8_gsl_shuping'],check=True,timeout=12)
 subprocess.run(['insmod',str(candidate)],check=True,timeout=15);time.sleep(2)
 current=Path('/sys/module/f8_gsl_shuping/srcversion').read_text().strip()
 assert current=='B769C22C37A1C4330D85F05'
 assert Path('/sys/bus/i2c/devices/4-0040/driver').resolve().name=='f8-gsl-shuping'
 out.update(stage='loaded_for_normal_desktop_use',srcversion=current)
 print(json.dumps(out,indent=2))
except BaseException:
 subprocess.run(['/usr/bin/python3',str(restore)],check=True,timeout=35)
 subprocess.run(['systemctl','stop',timer+'.timer'],check=True,timeout=8)
 raise
finally:(W/'load-result.json').write_text(json.dumps(out,indent=2)+'\n')
