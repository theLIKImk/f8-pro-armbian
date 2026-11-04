"""Step through GPU OPPs, sampling real frequency/voltage; bounded rollback."""
import collections,json,os,re,signal,subprocess,time
from pathlib import Path
assert os.geteuid()==0 and os.environ.get('SUDO_USER')=='likimk'
assert Path('/proc/device-tree/chosen/f8-gpu-trial').read_bytes()==b'p3-1000mhz\0'
d=Path('/sys/class/devfreq/fb000000.gpu-panthor');lo=d/'min_freq';hi=d/'max_freq'
before={'min':lo.read_text().strip(),'max':hi.read_text().strip(),'governor':(d/'governor').read_text().strip()}
assert before=={'min':'200000000','max':'400000000','governor':'simple_ondemand'}
zone=next(p for p in Path('/sys/class/thermal').glob('thermal_zone*') if (p/'type').read_text().strip()=='gpu-thermal')
reg=next(p for p in Path('/sys/class/regulator').glob('*') if (p/'name').exists() and (p/'name').read_text().strip()=='vdd_gpu_s0')
assert int((zone/'temp').read_text())<65000
u=['runuser','-u','likimk','--','env','XDG_RUNTIME_DIR=/run/user/1602','DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1602/bus','WAYLAND_DISPLAY=wayland-0']
base=['glmark2-es2-wayland','--off-screen','--frame-end','finish','--size','1280x720']
out={'before':before,'samples':[],'runs':[]};proc=None;start=time.monotonic();unit='f8-gpu-p3-restore-'+str(int(time.time()))
recovery='from pathlib import Path;Path('+repr(str(lo))+').write_text("200000000");Path('+repr(str(hi))+').write_text("400000000")'
subprocess.run(['systemd-run','--quiet','--unit='+unit,'--on-active=65s','/usr/bin/python3','-c',recovery],capture_output=True,check=True,timeout=8)
def run(mhz,uv,validate=False):
 global proc
 freq=mhz*1000000;hi.write_text(str(freq));lo.write_text(str(freq))
 time.sleep(.2)
 args=base+(['--validate','-b','build','-b','texture'] if validate else ['-b','terrain:duration=3'])
 proc=subprocess.Popen(u+args,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True)
 deadline=time.monotonic()+18;label=str(mhz)+('-validate' if validate else '');active_samples=0
 while proc.poll() is None:
  temp=int((zone/'temp').read_text());actual=int((d/'cur_freq').read_text());volt=int((reg/'microvolts').read_text())
  clk=Path('/sys/kernel/debug/clk/clk_summary').read_text();scmi=next(s for s in clk.splitlines() if 'scmi_clk_gpu ' in s)
  out['samples'].append({'run':label,'gpu_hz':actual,'microvolts':volt,'temp_mc':temp,'scmi_clock':scmi})
  if temp>=75000 or time.monotonic()>deadline or time.monotonic()-start>53:raise RuntimeError('GPU bounded test stopped at temperature/time limit')
  # Runtime-suspended GPU and shader compilation can legitimately show
  # the 200 MHz suspend clock. Verify the real target when rendering.
  if actual==freq and int(scmi.split()[4])==freq:
   active_samples+=1
   assert uv<=volt<=850000,(mhz,uv,volt)
  time.sleep(.5)
  # Read a clock while the GPU is active: the cached devfreq target alone
  # would not establish the real SCMI clock rate.
 stdout,stderr=proc.communicate(timeout=2);rc=proc.returncode;proc=None
 out['runs'].append({'mhz':mhz,'validation':validate,'exit':rc,'active_target_samples':active_samples,'stdout':stdout,'stderr':stderr})
 assert rc==0 and 'Mali-G610' in stdout,(rc,stdout,stderr)
 if not validate:assert active_samples>=1,('No active target clock observed',mhz)
 lo.write_text('200000000')
try:
 for mhz,uv in [(500,675000),(600,675000),(700,700000),(800,750000),(900,800000),(1000,850000)]:run(mhz,uv)
 run(1000,850000,True)
except Exception as e:out['error']=str(e)
finally:
 if proc is not None:
  try:os.killpg(proc.pid,signal.SIGTERM);proc.communicate(timeout=3)
  except Exception:
   try:os.killpg(proc.pid,signal.SIGKILL)
   except ProcessLookupError:pass
 lo.write_text(before['min']);hi.write_text(before['max'])
 subprocess.run(['systemctl','stop',unit+'.timer'],capture_output=True,timeout=8)
out['restored']={n:(d/n).read_text().strip() for n in ['min_freq','max_freq','governor','cur_freq']}
out['max_temp_celsius']=max(s['temp_mc'] for s in out['samples'])/1000 if out['samples'] else None
log=subprocess.run(['journalctl','-k','-b','--no-pager'],capture_output=True,text=True,timeout=10).stdout
out['faults']=[s for s in log.splitlines() if re.search(r'\bOops:|\bBUG:|gpu.*(fault|hang|timeout)|panthor.*(error|reset)',s,re.I)]
print(json.dumps(out,indent=2))
