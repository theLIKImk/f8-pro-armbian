#!/bin/sh
echo 'Disabled: CIF hot unbind caused a kernel oops on C1; use a fresh boot.' >&2
exit 1
set -eu
python3 -I - <<'PY'
import json,subprocess
from pathlib import Path
assert Path('/sys/bus/i2c/devices/5-0037/driver').resolve().name=='gc5035'
dev=Path('/sys/bus/platform/devices/rkcif-mipi-lvds2');driver=(dev/'driver').resolve()
assert driver.name=='rkcif',str(driver)
(driver/'unbind').write_text(dev.name+'\n')
try:(driver/'bind').write_text(dev.name+'\n')
except Exception:
 if not (dev/'driver').exists():(driver/'bind').write_text(dev.name+'\n')
 raise
result={'media':{},'bindings':{}}
for name in ['csi2-dphy1','mipi2-csi2','rkcif-mipi-lvds2','rkcif-mipi-lvds2-sditf','rkisp1-vir0']:
 p=Path('/sys/bus/platform/devices')/name/'driver';result['bindings'][name]=p.resolve().name if p.exists() else None
for p in Path('/dev').glob('media*'):
 r=subprocess.run(['media-ctl','-d',str(p),'-p'],capture_output=True,text=True,timeout=10);result['media'][str(p)]=r.stdout
result['logs']=subprocess.check_output(['sh','-c','dmesg | tail -40'],text=True)
print(json.dumps(result,indent=2))
PY
