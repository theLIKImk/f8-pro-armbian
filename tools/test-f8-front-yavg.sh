#!/bin/sh
python3 - << 'PYEOF'
data = open('/tmp/f8-front-a.raw','rb').read()
y = data[:640*480]
avg = sum(y)/len(y)
print('Y avg=%.1f min=%d max=%d' % (avg, min(y), max(y)))
print('judge:', 'TOO_DARK' if avg < 40 else 'TOO_BRIGHT' if avg > 220 else 'ACCEPTABLE')
PYEOF
echo MARKER_DONE
