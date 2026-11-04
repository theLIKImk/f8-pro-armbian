set -eu
python3 - <<'PY'
from pathlib import Path
import json,time
w=Path('/home/alarm/f8-pro-builds/kwin-6.7.5-v73ibK4G')
start=int((w/'thermal-history.csv').read_text().splitlines()[0].split(',')[0])
objects=list((w/'src/build').rglob('*.o'))
old=[p for p in objects if p.stat().st_mtime<start]
new=[p for p in objects if p.stat().st_mtime>=start]
print(json.dumps({'resume_start_epoch':start,'retained_objects':len(old),'objects_since_resume':len(new),'all_objects':len(objects),'latest_objects':[str(p.relative_to(w)) for p in sorted(new,key=lambda p:p.stat().st_mtime)[-3:]]},indent=2))
PY
