#!/bin/sh
set -eu
python3 -I - <<'PY'
import json,re
from pathlib import Path
claims={}
for p in Path('/sys/kernel/debug/pinctrl').glob('*/pinmux-pins'):
    claims[str(p)]=[s for s in p.read_text().splitlines() if re.search(r'^pin (114|138) \(',s)]
print(json.dumps({'pinmux':claims,'backlight':{p.name:{n:(p/n).read_text().strip() for n in ['brightness','actual_brightness','max_brightness']} for p in Path('/sys/class/backlight').glob('*')}},indent=2))
PY
