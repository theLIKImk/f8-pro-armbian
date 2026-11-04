#!/usr/bin/python3
"""F8 speaker-only gentle low-volume curve; no microphone/Bluetooth changes."""
import json,os,signal,subprocess,time
from pathlib import Path
HARDWARE='alsa_output.platform-es8388-sound.HiFi__Speaker__sink'
VIRTUAL='f8-speaker-volume'
CONFIG='/usr/share/f8-pro/audio/f8-speaker-volume.conf'
state=Path(os.environ.get('XDG_STATE_HOME',str(Path.home()/'.local/state')))/'f8-speaker-volume/state.json'
stopping=False

def cmd(*args):
 r=subprocess.run(args,capture_output=True,text=True,timeout=5)
 if r.returncode:raise RuntimeError(' '.join(args[:2])+': '+r.stderr.strip())
 return r.stdout.strip()
def sinks():return {s['name']:s for s in json.loads(cmd('pactl','--format=json','list','sinks'))}
def levels(s):return [v['value']/65536 for v in s['volume'].values()]
def setvol(name,v):cmd('pactl','set-sink-volume',name,*[str(round(x*65536)) for x in v])
def stop(*args):
 global stopping
 stopping=True
signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGINT,stop)
child=None;last=None;ready=False
try:
 for _ in range(60):
  if stopping:break
  try:
   old=sinks().get(HARDWARE)
   if old:break
  except (RuntimeError,subprocess.TimeoutExpired):pass
  time.sleep(.5)
 else:raise RuntimeError('F8 speaker is unavailable')
 if not stopping:
  initial={'volume':[x**2 for x in levels(old)],'mute':old['mute']}
  try:
   saved=json.loads(state.read_text())
   if len(saved['volume'])==2 and all(isinstance(x,(int,float)) and 0<=x<=1 for x in saved['volume']) and isinstance(saved['mute'],bool):initial=saved
  except (OSError,ValueError,KeyError,TypeError):pass
  default=cmd('pactl','get-default-sink')
  child=subprocess.Popen(['/usr/bin/pipewire','-c',CONFIG])
  for _ in range(40):
   if child.poll() is not None:raise RuntimeError('Filter process exited')
   if VIRTUAL in sinks():break
   time.sleep(.1)
  else:raise RuntimeError('F8 volume sink not created')
  cmd('pactl','set-sink-mute',VIRTUAL,'1')
  setvol(VIRTUAL,initial['volume'])
  for stream in json.loads(cmd('pactl','--format=json','list','sink-inputs')):
   # Only move applications directly on the built-in sink; never move our output.
   if stream['sink']==old['index'] and stream.get('properties',{}).get('node.name')!='f8-speaker-volume-output':
    cmd('pactl','move-sink-input',str(stream['index']),VIRTUAL)
  if default in (HARDWARE,VIRTUAL):cmd('pactl','set-default-sink',VIRTUAL)
  setvol(HARDWARE,[1,1]);cmd('pactl','set-sink-mute',HARDWARE,'0')
  cmd('pactl','set-sink-mute',VIRTUAL,'1' if initial['mute'] else '0')
  ready=True
  print('F8 speaker curve ready',flush=True)
  while not stopping:
   if child.poll() is not None:raise RuntimeError('Filter process exited')
   v=sinks().get(VIRTUAL)
   if v:
    last={'volume':[min(1,max(0,x)) for x in levels(v)],'mute':v['mute']}
    if last!=getattr(sinks,'saved',None):
     state.parent.mkdir(parents=True,exist_ok=True)
     temp=state.with_suffix('.tmp');temp.write_text(json.dumps(last));temp.replace(state)
     sinks.saved=last
   time.sleep(1)
finally:
 # Restore an equivalent physical level BEFORE terminating the filter, so fallback
 # applications cannot land on a 100% hardware sink after a normal service stop.
 if child is not None:
  try:
   if ready:
    v=sinks().get(VIRTUAL)
    if v:last={'volume':levels(v),'mute':v['mute']}
    restore=last or initial
    setvol(HARDWARE,[min(1,x)**0.5 for x in restore['volume']])
    cmd('pactl','set-sink-mute',HARDWARE,'1' if restore['mute'] else '0')
   else:
    setvol(HARDWARE,levels(old));cmd('pactl','set-sink-mute',HARDWARE,'1' if old['mute'] else '0')
   if cmd('pactl','get-default-sink')==VIRTUAL:cmd('pactl','set-default-sink',HARDWARE)
  except Exception as e:print('Volume restore:',e,flush=True)
  child.terminate()
  try:child.wait(timeout=4)
  except subprocess.TimeoutExpired:child.kill()
