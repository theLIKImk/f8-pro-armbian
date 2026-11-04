set -eu
work=/home/alarm/f8-pro-builds/kwin-6.7.5-v73ibK4G
printf 'KWIN LATEST\n'
tail -n 4 "$work/build.log"
printf 'NATIVE BINARIES\n'
for file in "$work/src/build/bin/kwin_wayland" "$work/src/build/bin/libkwin.so"; do
    if [ -f "$file" ]; then ls -lh "$file"; fi
done
printf 'AUTOGEN SETTINGS\n'
python3 - <<'PY'
import json
from pathlib import Path
p=Path('/home/alarm/f8-pro-builds/kwin-6.7.5-v73ibK4G/src/build')
rows=[json.loads(f.read_text())['PARALLEL'] for f in p.rglob('AutogenInfo.json')]
print('Autogen values:',sorted(set(rows)), 'targets:',len(rows))
PY
