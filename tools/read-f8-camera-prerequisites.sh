#!/bin/sh
set -eu
python3 -I - <<'PY'
import hashlib,json,subprocess
from pathlib import Path
def run(args):
    try:
        p=subprocess.run(args,capture_output=True,text=True,timeout=12)
        return {'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr}
    except Exception as e:return {'error':str(e)}
pins='\n'.join(p.read_text() for p in Path('/sys/kernel/debug/pinctrl').glob('*/pinmux-pins'))
selected={}
for pin in [36,38,39,42,43,46,47,102]:
    line=next(s for s in pins.splitlines() if s.startswith(f'pin {pin} ('))
    assert '(MUX UNCLAIMED) (GPIO UNCLAIMED)' in line,line
    selected[str(pin)]=line
drivers={}
for name in ['gc5035','ov8858','dw9714']:
    info=run(['modinfo',name]);assert info['exit']==0,info
    assert '6.1.115-vendor-rk35xx SMP mod_unload modversions aarch64' in info['stdout']
    p=Path(next(s.split(':',1)[1].strip() for s in info['stdout'].splitlines() if s.startswith('filename:')))
    drivers[name]={'modinfo':info,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
print(json.dumps({'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'camera_pins_unclaimed':selected,'drivers':drivers,
 'tools':run(['sh','-c','command -v media-ctl; command -v v4l2-ctl']),
 'rkaiq_packages':run(['sh','-c',"apt-cache search 'rkaiq|camera-engine' | head -20"]),
 'tool_candidates':run(['apt-cache','policy','gstreamer1.0-tools','libcamera-tools']),
 'services':run(['systemctl','is-active','f8-motion','iio-sensor-proxy','f8-compass','f8-bluetooth','f8-usb-otg','sddm'])},indent=2))
PY
