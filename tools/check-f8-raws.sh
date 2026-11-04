#!/bin/bash
python3 - << 'PYEOF'
import glob, os
# 找最近的 raw 输出
for f in ['/tmp/f8-rear-now.raw', '/tmp/f8-front-a.raw', '/tmp/f8-front-b.raw']:
    if os.path.exists(f):
        data = open(f,'rb').read()
        y = data[:640*480]
        avg = sum(y)/len(y)
        v = 'DARK' if avg < 40 else ('BRIGHT' if avg > 220 else 'OK')
        print(f, 'len', len(data), 'Yavg %.1f' % avg, v)
    else:
        print(f, 'missing')
PYEOF
echo MARKER_DONE
