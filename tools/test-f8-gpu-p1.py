"""Bounded same-scene 200/400 MHz cap comparison; restores the original cap."""
import collections,json,os,re,subprocess,time
from pathlib import Path
assert os.geteuid()==0 and os.environ.get('SUDO_USER')=='likimk'
assert Path('/proc/device-tree/chosen/f8-gpu-trial').read_bytes()==b'p1-400mhz\0'
dev=Path('/sys/class/devfreq/fb000000.gpu-panthor');cap=dev/'max_freq'
old=cap.read_text().strip();assert old=='400000000'
assert (dev/'min_freq').read_text().strip()=='200000000'
zone=next(p for p in Path('/sys/class/thermal').glob('thermal_zone*') if (p/'type').read_text().strip()=='gpu-thermal')
assert int((zone/'temp').read_text())<65000
u=['runuser','-u','likimk','--','env','XDG_RUNTIME_DIR=/run/user/1602','DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1602/bus','WAYLAND_DISPLAY=wayland-0']
base=['glmark2-es2-wayland','--off-screen','--frame-end','finish','--size','1280x720']
out={'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'initial_max_freq':old,'scene':'terrain','size':'1280x720','samples':[],'runs':[]}
unit='f8-gpu-p1-restore-'+str(int(time.time()))
restore='from pathlib import Path;Path('+repr(str(cap))+').write_text('+repr(old)+')'
subprocess.run(['systemd-run','--quiet','--unit='+unit,'--on-active=65s','/usr/bin/python3','-c',restore],check=True,capture_output=True,timeout=8)
started=time.monotonic();proc=None
def run(limit,duration,label):
 global proc
 cap.write_text(str(limit));args=u+base+['-b','terrain:duration='+str(duration)]
 proc=subprocess.Popen(args,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,start_new_session=True)
 deadline=time.monotonic()+22
 while proc.poll() is None:
  temp=int((zone/'temp').read_text());freq=int((dev/'cur_freq').read_text())
  out['samples'].append({'run':label,'elapsed':round(time.monotonic()-started,2),'temp_millicelsius':temp,'freq_hz':freq})
  if temp>=75000 or time.monotonic()>deadline or time.monotonic()-started>52:
   raise RuntimeError('Stopped bounded test: temperature or time limit')
  time.sleep(.5)
 stdout,stderr=proc.communicate(timeout=2);rc=proc.returncode;proc=None
 out['runs'].append({'label':label,'cap_hz':limit,'exit':rc,'stdout':stdout,'stderr':stderr})
 assert rc==0,(label,rc,stderr)
 assert 'llvmpipe' not in stdout.lower() and 'Mali' in stdout,'Unexpected renderer'
try:
 run(200000000,2,'warmup')
 run(200000000,6,'cap200')
 run(400000000,6,'cap400')
except Exception as e:out['error']=str(e)
finally:
 if proc is not None:
  import signal
  try:os.killpg(proc.pid,signal.SIGTERM);proc.communicate(timeout=3)
  except Exception:
   try:os.killpg(proc.pid,signal.SIGKILL)
   except ProcessLookupError:pass
 cap.write_text(old);out['restored_max_freq']=cap.read_text().strip()
 subprocess.run(['systemctl','stop',unit+'.timer'],capture_output=True,timeout=8)
out['frequency_counts']={label:dict(collections.Counter(x['freq_hz'] for x in out['samples'] if x['run']==label)) for label in ['warmup','cap200','cap400']}
out['max_temp_celsius']=max(x['temp_millicelsius'] for x in out['samples'])/1000 if out['samples'] else None
log=subprocess.run(['journalctl','-k','-b','--no-pager'],capture_output=True,text=True,timeout=10).stdout
out['fault_lines']=[s for s in log.splitlines() if re.search(r'gpu.*(fault|hang|timeout)|panthor.*(error|reset)|\bOops:|\bBUG:',s,re.I)]
print(json.dumps(out,indent=2))
