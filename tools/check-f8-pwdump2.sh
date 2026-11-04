#!/bin/sh
export XDG_RUNTIME_DIR=/run/user/1601
timeout 10 pw-dump > /tmp/f8-dump.json 2>/dev/null
wc -l /tmp/f8-dump.json
python3 - <<'PY'
import json
data = json.load(open('/tmp/f8-dump.json'))
for o in data:
    p = o.get('props', {})
    mc = p.get('media.class', '')
    if 'Audio' in mc:
        print(mc, '|', p.get('node.description') or p.get('node.name'))
PY
echo DONE
