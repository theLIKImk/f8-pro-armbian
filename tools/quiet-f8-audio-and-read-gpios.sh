#!/bin/sh
set -eu
python3 -I - <<'PY'
import json,re,subprocess
from pathlib import Path
stage=Path('/run/f8/audio-a1-quiet-01');stage.mkdir(exist_ok=False)
def cmd(args):
    r=subprocess.run(args,capture_output=True,text=True,timeout=15)
    return {'exit':r.returncode,'stdout':r.stdout,'stderr':r.stderr}
before=cmd(['amixer','-c','0','scontents'])
result={'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'before':before,
 'speaker_off':cmd(['amixer','-c','0','sset','Speaker','off']),
 'out2_off':cmd(['amixer','-c','0','sset','OUT2','off']),
 'speaker_gpio_state':cmd(['amixer','-c','0','sget','spk switch'])}
claims={}
for p in Path('/sys/kernel/debug/pinctrl').glob('*/pinmux-pins'):
    lines=[s for s in p.read_text().splitlines() if re.search(r'^pin (114|130|133) \(',s)]
    if lines:claims[str(p)]=lines
result['pinmux']=claims
gpio=Path('/sys/kernel/debug/gpio')
if gpio.exists():result['gpio_lines']=[s for s in gpio.read_text().splitlines() if any(re.search(r'gpio-\s*'+str(n)+r'\b',s) for n in [114,130,133])]
base=Path('/sys/firmware/devicetree/base')
result['motor_nodes']={}
for p in base.rglob('compatible'):
    raw=p.read_bytes()
    if b'vibrat' in raw or b'haptic' in raw:
        result['motor_nodes'][str(p.parent.relative_to(base))]={f.name:f.read_bytes().hex() for f in p.parent.iterdir() if f.is_file()}
result['card_gpio_properties']={}
for node in [base/'es8388-sound',base/'i2c@fec90000/es8388@11']:
    result['card_gpio_properties'][str(node.relative_to(base))]={p.name:p.read_bytes().hex() for p in node.iterdir() if p.is_file() and ('gpio' in p.name or 'pinctrl' in p.name)}
result['battery_touched']=False
(stage/'result.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
PY
