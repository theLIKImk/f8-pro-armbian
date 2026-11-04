"""Collect A3 runtime evidence without audible playback or battery changes."""
import json, subprocess
from pathlib import Path
P=Path(__file__).resolve().parents[1]
dest=P/'local/hardware/armbian-native-audio-a3-20261101-01'
dest.mkdir(exist_ok=True)
def capture(name, script):
    out=dest/(name+'.json')
    assert not out.exists(), 'Preserve existing evidence'
    r=subprocess.run(['python3',str(P/'tools/ssh-f8-desktop.py'),'--address','192.168.1.227','--script',str(script),'--sudo'],capture_output=True,text=True,timeout=100)
    assert r.returncode==0,r.stderr[-1600:]
    d=json.loads(r.stdout);out.write_text(json.dumps(d,indent=2)+'\n')
    return d
runner=dest/'dt-runner.sh'
runner.write_text('''#!/bin/sh
set -eu
python3 -I - <<'PY'
import json
from pathlib import Path
p=Path('/sys/firmware/devicetree/base')
codec=p/'i2c@fec90000/es8388@11'
gate=p/'clocks/mclkout-i2s0@fd58c318'
clock=(codec/'clocks').read_bytes();handle=(gate/'phandle').read_bytes()
assert len(clock)==4 and clock==handle,'Not A3 clock reference'
boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip()
assert boot!='0c6411d0-54bf-4a57-98d6-0e1cac9a7fd7','Expected a new boot'
print(json.dumps({'boot_id':boot,'codec_clock_uses_io_provider':True,'provider_phandle':int.from_bytes(handle,'big'),'assigned_rate':int.from_bytes((codec/'assigned-clock-rates').read_bytes(),'big')}))
PY
''')
print(json.dumps({'dt':capture('dt',runner)}),flush=True)
for name,script in [('backlight','read-f8-backlight-ownership.sh'),('desktop','verify-f8-native-desktop.sh'),('audio','read-f8-audio-runtime.sh')]:
    d=capture(name,P/'tools'/script)
    if name=='backlight':
        claims='\n'.join(line for lines in d['pinmux'].values() for line in lines)
        assert 'pin 138 (gpio4-10): febf0020.pwm' in claims and 'group pwm14m1-pins' in claims
        assert 'pin 114 (gpio3-18): febf0020.pwm' not in claims
    print(json.dumps({name:d if name!='audio' else {k:d.get(k) for k in ['cards','devices','sound_log']}}),flush=True)
silent=dest/'silent-clock-runner.sh'
silent.write_text((P/'tools/probe-f8-a2-silent-clock.sh').read_text().replace('audio-a2-silent-clock-01','audio-a3-silent-clock-01'))
d=capture('silent-clock-01',silent)
print(json.dumps({'silent_clock':{k:d.get(k) for k in ['boot_id','hw_params','i2s_clocks','aplay','restore']}}),flush=True)
