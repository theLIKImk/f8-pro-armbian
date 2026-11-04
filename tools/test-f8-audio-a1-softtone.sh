#!/bin/sh
set -eu
python3 -I - <<'PY'
import json,math,struct,subprocess,wave
from pathlib import Path
assert Path('/run/user/1601').stat().st_uid==1601
stage=Path('/run/user/1601/f8-audio-a1-softtone-02');stage.mkdir(exist_ok=False)
def cmd(args,timeout=15,check=True):
    r=subprocess.run(args,capture_output=True,text=True,timeout=timeout)
    if check and r.returncode:raise RuntimeError('Command failed: '+args[0]+' '+r.stderr[-800:])
    return {'exit':r.returncode,'stdout':r.stdout,'stderr':r.stderr}
assert 'ES8323' in Path('/proc/asound/pcm').read_text()
prefix=['runuser','-u','f8test','--','env','XDG_RUNTIME_DIR=/run/user/1601','DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1601/bus']
helptext=cmd(prefix+['pw-play','--help']);assert '--volume' in helptext['stdout']+helptext['stderr']
wav=stage/'soft-left-right.wav';rate=48000
with wave.open(str(wav),'wb') as w:
    w.setnchannels(2);w.setsampwidth(2);w.setframerate(rate)
    frames=bytearray()
    for i in range(rate*2):
        t=i/rate;left=right=0
        for channel,start,end,freq in [(0,0.1,0.7,440),(1,1.0,1.6,660)]:
            if start<=t<end:
                ramp=min(1,(t-start)/0.025,(end-t)/0.025)
                value=int(32767*0.2*ramp*math.sin(2*math.pi*freq*t))
                if channel==0:left=value
                else:right=value
        frames.extend(struct.pack('<hh',left,right))
    w.writeframes(frames)
wav.chmod(0o644);stage.chmod(0o755)
state=stage/'before.state';cmd(['alsactl','-f',str(state),'store','0'])
result={'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'before':cmd(['amixer','-c','0','scontents']),
        'duration_seconds':2,'wave_peak':0.2,'stream_volume':0.35,'physical_sound_heard':None}
try:
    result['output_gain']=cmd(['amixer','-c','0','sset','Output 2','24'])
    result['output_route']=cmd(['amixer','-c','0','sset','OUT2','on'])
    # Speaker amplifier follows the existing DAPM event; do not force its GPIO.
    result['play']=cmd(prefix+['pw-play','--volume=0.35',str(wav)],timeout=10,check=False)
    result['sound_log']=cmd(['sh','-c',"dmesg | grep -Ei 'es83|asoc|i2s|underrun' | tail -50"],check=False)
finally:
    result['restore']=cmd(['alsactl','-f',str(state),'restore','0'],check=False)
    result['after']=cmd(['amixer','-c','0','scontents'],check=False)
    (stage/'result.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
PY
