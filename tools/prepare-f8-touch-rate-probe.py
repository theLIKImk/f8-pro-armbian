"""Generate a RAM-only timing trial with an independently scheduled rollback."""
import argparse,base64,hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--period',type=int,choices=[252,157,128,122],default=252);p.add_argument('--attempt',type=int,choices=[1,2],default=1);a=p.parse_args()
O=P/f'outputs/armbian/f8-touch-rate-p{a.period}';m=json.loads((O/'module-check.json').read_text());data=(O/'f8_gsl_shuping.ko').read_bytes()
assert hashlib.sha256(data).hexdigest()==m['sha256'] and m['import_crcs_identical_to_actual_verified_baseline']
capture=(P/f'local/hardware/touch-rate-p{a.period}-{a.attempt}-runner.py').read_bytes()
worktag=f'p{a.period}-load'+('' if a.attempt==1 else str(a.attempt))
rollback='''import hashlib,json,subprocess,time
from pathlib import Path
old=Path('/usr/libexec/f8-pro/f8_gsl_shuping.ko')
assert hashlib.sha256(old.read_bytes()).hexdigest()=='bb8fd9db0bf16972e6760ca9d8ba8489e91a516c31269fc770346fe75d7a505d'
base=subprocess.check_output(['modinfo','-F','srcversion',str(old)],text=True).strip()
loaded=Path('/sys/module/f8_gsl_shuping/srcversion')
current=loaded.read_text().strip() if loaded.exists() else None
assert current in [None,base,EXPECTED_VERSION],'Another driver version is active; preserve it'
out={'started':time.time(),'previous_srcversion':current,'restored':False}
if current!=base:
 if current is not None:subprocess.run(['rmmod','f8_gsl_shuping'],check=True,timeout=12)
 subprocess.run(['insmod',str(old)],check=True,timeout=15);time.sleep(2)
assert loaded.read_text().strip()==base
assert Path('/sys/bus/i2c/devices/4-0040/driver').resolve().name=='f8-gsl-shuping'
out.update(restored=True,srcversion=base,persistent_asset_changed=False)
Path(RESULT_PATH).write_text(json.dumps(out,indent=2)+'\\n');print(json.dumps(out))
'''.replace('EXPECTED_VERSION',repr(m['srcversion'])).replace('RESULT_PATH',repr(f'/var/lib/f8-pro/touch-rate/{worktag}/restore-result.json'))
compile(rollback,'rollback','exec')
code='''import base64,hashlib,json,os,subprocess,time
from pathlib import Path
assert os.geteuid()==0 and os.environ.get('SUDO_USER')=='likimk'
assert os.uname().release=='6.1.115-vendor-rk35xx'
assert Path('/proc/device-tree/model').read_bytes().startswith(b'F8-PRO')
old=Path('/usr/libexec/f8-pro/f8_gsl_shuping.ko')
assert hashlib.sha256(old.read_bytes()).hexdigest()=='bb8fd9db0bf16972e6760ca9d8ba8489e91a516c31269fc770346fe75d7a505d'
assert Path('/sys/module/f8_gsl_shuping/srcversion').read_text().strip()==subprocess.check_output(['modinfo','-F','srcversion',str(old)],text=True).strip()
assert not [l for l in Path('/sys/kernel/tracing/kprobe_events').read_text().splitlines() if 'f8_gsl_shuping:' in l]
assert not Path('/sys/kernel/tracing/instances/f8rate_baseline1').exists(),'Baseline capture is still active'
W=Path(WORKDIR);assert not W.exists();W.mkdir(parents=True);W.chmod(0o700)
candidate=W/'f8_gsl_shuping.ko';data=base64.b64decode(MODULE_DATA);assert hashlib.sha256(data).hexdigest()==EXPECTED_SHA
candidate.write_bytes(data);candidate.chmod(0o644)
restore=W/'restore.py';restore.write_bytes(base64.b64decode(ROLLBACK_DATA));restore.chmod(0o700)
timer=TIMER_NAME
r=subprocess.run(['systemd-run','--unit='+timer,'--on-active=180s','--timer-property=AccuracySec=1s','--property=RuntimeMaxSec=45','/usr/bin/python3',str(restore)],capture_output=True,text=True,timeout=10);assert r.returncode==0,r.stderr
out={'period_candidate':PERIOD,'original_period':280,'auto_rollback_seconds':180,'timer':timer+'.timer','persistent_asset_changed':False}
try:
 subprocess.run(['rmmod','f8_gsl_shuping'],check=True,timeout=12)
 subprocess.run(['insmod',str(candidate)],check=True,timeout=15);time.sleep(2)
 assert Path('/sys/module/f8_gsl_shuping/srcversion').read_text().strip()==EXPECTED_VERSION
 assert Path('/sys/bus/i2c/devices/4-0040/driver').resolve().name=='f8-gsl-shuping'
 capture=W/'open-capture.py';capture.write_bytes(base64.b64decode(CAPTURE_DATA));capture.chmod(0o700)
 r=subprocess.run(['/usr/bin/python3',str(capture)],capture_output=True,text=True,timeout=35);assert r.returncode==0,r.stderr
 out.update(stage='trial_loaded_capture_waiting',srcversion=EXPECTED_VERSION,capture=json.loads(r.stdout),hardware_rate_verified=False)
 print(json.dumps(out,indent=2))
except BaseException:
 subprocess.run(['/usr/bin/python3',str(restore)],check=True,timeout=35)
 subprocess.run(['systemctl','stop',timer+'.timer'],check=True,timeout=8)
 raise
finally:(W/'load-result.json').write_text(json.dumps(out,indent=2)+'\\n')
'''
values={'WORKDIR':repr(f'/var/lib/f8-pro/touch-rate/{worktag}'),'TIMER_NAME':repr('f8-touch-rate-rollback-p'+str(a.period)+('' if a.attempt==1 else '-'+str(a.attempt))),'MODULE_DATA':repr(base64.b64encode(data).decode()),'EXPECTED_SHA':repr(m['sha256']),'EXPECTED_VERSION':repr(m['srcversion']),'ROLLBACK_DATA':repr(base64.b64encode(rollback.encode()).decode()),'CAPTURE_DATA':repr(base64.b64encode(capture).decode()),'PERIOD':str(a.period)}
for k in sorted(values,key=len,reverse=True):code=code.replace(k,values[k])
compile(code,'probe-runner','exec');(P/f'local/hardware/touch-rate-{worktag}-runner.py').write_text(code)
print('Probe and independent rollback prepared')
