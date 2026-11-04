set -eu
work=/home/alarm/f8-pro-builds/kwin-6.7.5-v73ibK4G
[ "$(id -u)" = 1000 ]
if pgrep -x makepkg >/dev/null; then echo 'A makepkg is still active'; exit 3; fi
cp -n "$work/src/build/CMakeCache.txt" "$work/CMakeCache.before-autogen-limit.txt"
cmake -S "$work/src/kwin-6.7.5" -B "$work/src/build" -DCMAKE_AUTOGEN_PARALLEL=1 >"$work/autogen-limit-configure.log" 2>&1
python3 - <<'PY'
from pathlib import Path
import json
work=Path('/home/alarm/f8-pro-builds/kwin-6.7.5-v73ibK4G')
rows=[json.loads(p.read_text())['PARALLEL'] for p in (work/'src/build').rglob('AutogenInfo.json')]
assert rows and set(rows)=={1},set(rows)
record={'setting':'CMAKE_AUTOGEN_PARALLEL','before':8,'after':1,'verified_autogen_targets':len(rows),'scope':'Only this native build cache; source and PKGBUILD unchanged','reason':'Bound Qt MOC worker count independently of main make parallelism'}
(work/'autogen-limit.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps(record,indent=2))
PY
