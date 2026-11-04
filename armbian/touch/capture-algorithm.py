"""Isolated, temporary kprobe of touch algorithm INPUT, paired with evdev capture.
No memory writes to the touchscreen or to algorithm state; no input grabbing.
"""
import json,os,signal,subprocess,time
from pathlib import Path
T=Path('/sys/kernel/tracing');I=T/'instances/f8touch_r3'
W=Path('/var/lib/f8-pro/touch-diagnostic/r3');W.mkdir(parents=True,exist_ok=True);W.chmod(0o700)
definition='p:f8touch_r3/raw f8_gsl_shuping:gsl_alg_id_main count=+120($arg1):u32 x=+0($arg1):u32[10] y=+40($arg1):u32[10] ids=+80($arg1):u32[10]'
assert 'f8touch_r3/' not in (T/'kprobe_events').read_text() and not I.exists()
registered=False;instance=False;child=None
def write(p,s):p.write_text(s+'\n')
def probe_command(s):
 # tracefs command file: no append seek and, crucially, no O_TRUNC.
 fd=os.open(T/'kprobe_events',os.O_WRONLY|os.O_CLOEXEC)
 try:os.write(fd,(s+'\n').encode())
 finally:os.close(fd)
def interrupted(*_):raise SystemExit('Bounded capture interrupted')
signal.signal(signal.SIGTERM,interrupted)
try:
 probe_command(definition)
 registered=True;I.mkdir();instance=True
 write(I/'tracing_on','0');write(I/'trace_clock','mono');write(I/'buffer_size_kb','4096')
 write(I/'events/f8touch_r3/raw/enable','1');write(I/'tracing_on','1')
 (W/'probe-definition.txt').write_text(definition+'\n')
 child=subprocess.Popen(['/usr/bin/python3','/var/lib/f8-pro/touch-diagnostic/capture-tracking-r3.py'])
 assert child.wait(timeout=370)==0,'Evdev capture failed'
finally:
 if child is not None and child.poll() is None:child.terminate();child.wait(timeout=3)
 if instance:
  write(I/'tracing_on','0');write(I/'events/f8touch_r3/raw/enable','0')
  output=W/'algorithm-input.txt';output.write_text((I/'trace').read_text());output.chmod(0o600)
  (W/'probe-profile.txt').write_text('\n'.join(l for l in (T/'kprobe_profile').read_text().splitlines() if 'f8touch_r3' in l))
  I.rmdir()
 if registered:
  probe_command('-:f8touch_r3/raw')
