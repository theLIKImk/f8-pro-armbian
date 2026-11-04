"""Reversible, single-module trial. Original boot asset stays untouched."""
import hashlib,json,subprocess,time,traceback
from pathlib import Path
W=Path('/var/lib/f8-pro/touch-t1');W.mkdir(parents=True,exist_ok=True);W.chmod(0o700)
old=Path('/usr/libexec/f8-pro/f8_gsl_shuping.ko')
new=Path('/usr/local/lib/f8-pro/experimental/f8_gsl_shuping_t1.ko')
out={'started':time.time(),'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'persistent_boot_asset_changed':False}
unloaded=False
def run(a,timeout=15):return subprocess.run(a,capture_output=True,text=True,timeout=timeout)
try:
 assert hashlib.sha256(old.read_bytes()).hexdigest()=='bb8fd9db0bf16972e6760ca9d8ba8489e91a516c31269fc770346fe75d7a505d'
 assert hashlib.sha256(new.read_bytes()).hexdigest()=='8910fe6644870cfa190d44d0915094e859243f6284d069e8fd8baabadf99add2'
 assert not [l for l in Path('/sys/kernel/tracing/kprobe_events').read_text().splitlines() if 'f8_gsl_shuping:' in l], 'Remove only our diagnostic probes first'
 assert Path('/sys/bus/i2c/devices/4-0040/driver').resolve().name=='f8-gsl-shuping'
 r=run(['rmmod','f8_gsl_shuping'],10);assert r.returncode==0,r.stderr;unloaded=True
 r=run(['insmod',str(new)]);assert r.returncode==0,r.stderr
 time.sleep(2)
 expected=subprocess.check_output(['modinfo','-F','srcversion',str(new)],text=True).strip()
 assert Path('/sys/module/f8_gsl_shuping/srcversion').read_text().strip()==expected
 assert Path('/sys/bus/i2c/devices/4-0040/driver').resolve().name=='f8-gsl-shuping'
 events=[p.name for p in Path('/sys/class/input').glob('event*') if (p/'device/name').read_text().strip()=='f8-gsl-shuping']
 assert len(events)==1,events
 out.update(stage='loaded_waiting_for_user_acceptance',srcversion=expected,event=events[0],hardware_firmware_payload_unchanged=True)
except BaseException:
 out.update(stage='failed',error=traceback.format_exc())
 if unloaded:
  if Path('/sys/module/f8_gsl_shuping').exists():out['remove_candidate']=run(['rmmod','f8_gsl_shuping'],10).returncode
  if not Path('/sys/module/f8_gsl_shuping').exists():
   r=run(['insmod',str(old)]);out['rollback']={'exit':r.returncode,'stderr':r.stderr}
 raise
finally:
 p=W/'load-result.json';p.write_text(json.dumps(out,indent=2)+'\n');p.chmod(0o600)
