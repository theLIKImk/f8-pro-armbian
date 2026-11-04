#!/bin/sh
set -eu
python3 -I - <<'PY'
import json,re,subprocess,time
from pathlib import Path
stage=Path('/run/f8/audio-a2-silent-clock-01');stage.mkdir(exist_ok=False)
def cmd(args,check=True):
    r=subprocess.run(args,capture_output=True,text=True,timeout=15)
    if check and r.returncode:raise RuntimeError(r.stderr[-800:])
    return {'exit':r.returncode,'stdout':r.stdout,'stderr':r.stderr}
state=stage/'before.state';cmd(['alsactl','-f',str(state),'store','0'])
result={'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'digital_samples':'all zero','battery_touched':False}
process=None
try:
    result['speaker_off']=cmd(['amixer','-c','0','sset','Speaker','off'])
    result['headphone_off']=cmd(['amixer','-c','0','sset','Headphone','off'])
    process=subprocess.Popen(['aplay','-q','-D','hw:0,0','-t','raw','-f','S16_LE','-r','48000','-c','2','-d','3','/dev/zero'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    hw=Path('/proc/asound/card0/pcm0p/sub0/hw_params')
    for _ in range(20):
        if process.poll() is not None:break
        if hw.exists() and 'format:' in hw.read_text():break
        time.sleep(0.05)
    result['hw_params']=hw.read_text() if hw.exists() else None
    s=Path('/proc/asound/card0/pcm0p/sub0/status');result['pcm_status']=s.read_text() if s.exists() else None
    result['pinmux']={str(p):[line for line in p.read_text().splitlines() if re.search(r'^pin (50|51|53|55|60) \(',line)] for p in Path('/sys/kernel/debug/pinctrl').glob('*/pinmux-pins')}
    clk=Path('/sys/kernel/debug/clk/clk_summary');result['i2s_clocks']=[s for s in clk.read_text().splitlines() if 'i2s0' in s.lower()] if clk.exists() else []
    stdout,stderr=process.communicate(timeout=8);result['aplay']={'exit':process.returncode,'stdout':stdout,'stderr':stderr}
finally:
    if process is not None and process.poll() is None:process.kill();process.wait()
    result['restore']=cmd(['alsactl','-f',str(state),'restore','0'],check=False)
    (stage/'result.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
PY
