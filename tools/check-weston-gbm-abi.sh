set -eu
python3 - <<'PY'
import subprocess,re,json
from pathlib import Path
prefix=Path('/opt/f8-pro/vendor-gpu-g13p0-20261028/lib')
exports=set(re.findall(r'\b(gbm_\w+)\b',subprocess.check_output(['nm','-D','--defined-only',str(prefix/'libgbm.so.1')],text=True)))
report={}
for path in Path('/usr/lib/libweston-15').glob('*.so'):
 table=subprocess.check_output(['readelf','--dyn-syms','--wide',str(path)],text=True)
 required=set(re.findall(r'UND\s+(gbm_\w+)',table))
 if required:report[path.name]={'gbm_required':sorted(required),'gbm_missing':sorted(required-exports)}
print(json.dumps(report,indent=2))
PY
printf '\nSYSTEM\n'
systemctl is-system-running
loginctl list-sessions --no-pager
