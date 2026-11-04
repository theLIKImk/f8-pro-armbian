#!/usr/bin/python3 -I
"""Fixed-purpose touch-rate controller. Independent timers recover unconfirmed settings."""
import fcntl,hashlib,json,os,re,secrets,stat,subprocess,sys,time
from pathlib import Path
ROOT=Path('/usr/libexec/f8-pro/touch-rate-panel')
BASE=Path('/usr/libexec/f8-pro/f8_gsl_shuping.ko')
MODULE=ROOT/'f8_gsl_rate.ko';PRIVATE=Path('/var/lib/f8-pro/touch-rate-panel')
PUBLIC=Path('/run/f8-touch-rate-control.json')
HELPER='/usr/libexec/f8-pro/touch-rate-control.py'

def run(args,timeout=15,check=True):
 r=subprocess.run(args,capture_output=True,text=True,timeout=timeout)
 if check and r.returncode:raise RuntimeError(r.stderr.strip() or 'Command failed')
 return r
def version():
 p=Path('/sys/module/f8_gsl_shuping/srcversion');return p.read_text().strip() if p.exists() else None
def boot():return Path('/proc/sys/kernel/random/boot_id').read_text().strip()
def load_state():
 p=PRIVATE/'state.json'
 if not p.exists():return {}
 d=json.loads(p.read_text());return d if d.get('boot_id')==boot() else {}
def visible(d):return {k:v for k,v in d.items() if k!='token'}
def store(d):
 d['boot_id']=boot();q=PRIVATE/'state.tmp';q.write_text(json.dumps(d));q.chmod(0o600);q.replace(PRIVATE/'state.json')
 q=PUBLIC.with_suffix('.tmp');assert not q.is_symlink();q.write_text(json.dumps(visible(d)));q.chmod(0o644);q.replace(PUBLIC)
def stop_timer(d):
 name=d.get('unit') or ''
 if re.fullmatch(r'f8-touch-rate-panel-[0-9a-f]{32}',name):run(['systemctl','stop',name+'.timer'],check=False,timeout=8)
def checked_meta():
 if os.uname().release!='6.1.115-vendor-rk35xx' or not Path('/proc/device-tree/model').read_bytes().startswith(b'F8-PRO'):raise RuntimeError('Unsupported device or kernel')
 m=json.loads((ROOT/'module.json').read_text())
 for p,digest in [(BASE,m['baseline_sha256']),(MODULE,m['sha256'])]:
  s=p.stat()
  if p.is_symlink() or s.st_uid!=0 or s.st_mode&0o022 or hashlib.sha256(p.read_bytes()).hexdigest()!=digest:raise RuntimeError('Module integrity check failed')
 return m
def known(m):
 if version() not in [None,m['srcversion'],m['baseline_srcversion']]:raise RuntimeError('Another touch driver is active; its configuration was preserved')
def restore_hardware(m):
 known(m)
 if version()!=m['baseline_srcversion']:
  if version() is not None:run(['rmmod','f8_gsl_shuping'])
  run(['insmod',str(BASE)]);time.sleep(.8)
 if version()!=m['baseline_srcversion']:raise RuntimeError('Original driver did not recover')
def original_state():return {'stage':'original','target_hz':None,'period':280,'pending_until':None,'unit':None,'token':None}

def main():
 if os.geteuid()!=0:raise RuntimeError('Administrator authorization required')
 args=sys.argv[1:]
 if args and args[0]=='apply' and len(args)==2 and re.fullmatch(r'[0-9]{2,3}',args[1]) and 60<=int(args[1])<=120:action='apply';hz=int(args[1])
 elif args in [['keep'],['restore']]:action=args[0]
 elif len(args)==2 and args[0]=='rollback' and re.fullmatch(r'[0-9a-f]{32}',args[1]):action='rollback'
 else:raise RuntimeError('Use apply 60..120, keep or restore')
 PRIVATE.mkdir(parents=True,exist_ok=True);PRIVATE.chmod(0o700)
 with (PRIVATE/'control.lock').open('a') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX)
  m=checked_meta();d=load_state()
  if action=='rollback':
   if d.get('token')!=args[1] or d.get('stage') not in ['applying','pending']:return {'ignored':True}
   restore_hardware(m);store(original_state());return {'restored':True}
  known(m)
  if action=='restore':
   stop_timer(d);restore_hardware(m);store(original_state());return visible(load_state())
  if action=='keep':
   if d.get('stage')!='pending':raise RuntimeError('No pending setting')
   if time.monotonic()>=d['pending_until']:
    restore_hardware(m);store(original_state());raise RuntimeError('Confirmation expired; restored original')
   if version()!=m['srcversion'] or int(Path('/sys/module/f8_gsl_shuping/parameters/period').read_text())!=d['period']:raise RuntimeError('Active setting changed')
   stop_timer(d);d.update(stage='kept',pending_until=None);store(d);return visible(d)
  table=json.loads((ROOT/'rate-map.json').read_text())['rates'];period=table[str(hz)]['period']
  if type(period)!=int or not 122<=period<=320:raise RuntimeError('Invalid timing table')
  stop_timer(d);token=secrets.token_hex(16);unit='f8-touch-rate-panel-'+token
  d={'stage':'applying','target_hz':hz,'period':period,'pending_until':time.monotonic()+45,'unit':unit,'token':token}
  store(d)
  try:
   run(['systemd-run','--collect','--unit='+unit,'--on-active=45s','--timer-property=AccuracySec=1s','--property=RuntimeMaxSec=40',HELPER,'rollback',token],timeout=10)
   if version() is not None:run(['rmmod','f8_gsl_shuping'])
   run(['insmod',str(MODULE),'period='+str(period)]);time.sleep(.8)
   if version()!=m['srcversion'] or int(Path('/sys/module/f8_gsl_shuping/parameters/period').read_text())!=period:raise RuntimeError('New driver did not load')
   if Path('/sys/bus/i2c/devices/4-0040/driver').resolve().name!='f8-gsl-shuping':raise RuntimeError('Touch device did not bind')
   d['stage']='pending';store(d);return visible(d)
  except BaseException:
   restore_hardware(m);stop_timer(d);store(original_state());raise

if __name__=='__main__':
 try:print(json.dumps({'ok':True,'state':main()}))
 except Exception as e:print(json.dumps({'ok':False,'error':str(e)}));sys.exit(1)
