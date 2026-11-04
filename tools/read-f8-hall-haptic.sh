#!/bin/sh
set -eu
python3 -I - <<'PY'
import json,subprocess
from pathlib import Path
out={'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip()}
for n,args in {'input':['cat','/proc/bus/input/devices'],'gpio':['cat','/sys/kernel/debug/gpio'],'pinmux':['sh','-c','cat /sys/kernel/debug/pinctrl/*/pinmux-pins | grep -E "pin (114|[0-9]+).*gpio3|pin 114|gpio3-18|hall|vibrat"'],'drivers':['sh','-c','ls /sys/bus/platform/drivers | grep -Ei "hall|vibr|gpio.*key|haptic"; command -v gpioinfo; command -v gpioget'],'config':['sh','-c','grep -E "CONFIG_(INPUT_GPIO|INPUT_FF|INPUT_UINPUT|INPUT_EVDEV|GPIOLIB|HALL)" /boot/config-$(uname -r)'],'chosen':['cat','/proc/cmdline']}.items():
 p=subprocess.run(args,capture_output=True,text=True,timeout=12);out[n]={'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr}
dt=Path('/sys/firmware/devicetree/base')
out['dt_nodes']={str(p.relative_to(dt)):{q.name:q.read_bytes().hex() for q in p.iterdir() if q.is_file()} for p in dt.rglob('*') if p.is_dir() and any(s in p.name.lower() for s in ['hall','vibrat','haptic'])}
print(json.dumps(out,indent=2))
PY
