#!/bin/sh
set -eu
python3 -I - <<'PY'
import json,subprocess
from pathlib import Path
lines=subprocess.check_output(['dmesg'],text=True).splitlines()
indices=[i for i,s in enumerate(lines) if 'WARNING:' in s or 'cut here' in s or 'Oops:' in s]
print(json.dumps({'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'tainted':Path('/proc/sys/kernel/tainted').read_text().strip(),'warnings':[lines[max(0,i-2):i+42] for i in indices if 'WARNING:' in lines[i]]},indent=2))
PY
