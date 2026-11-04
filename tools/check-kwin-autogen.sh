set -eu
python3 - <<'PY'
from pathlib import Path
import json
work=Path('/home/alarm/f8-pro-builds/kwin-6.7.5-v73ibK4G/src/build')
rows=[]
for p in work.rglob('AutogenInfo.json'):
    obj=json.loads(p.read_text())
    rows.append({'target':str(p.relative_to(work)),'parallel':obj.get('PARALLEL')})
print(json.dumps({'autogen_target_count':len(rows),'parallel_values':sorted(set(str(r['parallel']) for r in rows)),'samples':rows[-8:]},indent=2))
cache=(work/'CMakeCache.txt').read_text()
print('\n'.join(line for line in cache.splitlines() if 'AUTOGEN_PARALLEL' in line))
PY
