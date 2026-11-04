#!/bin/bash
# fix v= line swallowed by comment
python3 - << 'PYEOF'
import re
src = open('/tmp/f8ph.py').read()
src = src.replace("# ??? 0x00", "#")
m = re.search(r'#.*\n_, _, off_struct', src)
if m:
    src = src.replace(m.group(0), 'v = struct.unpack(">10I", data[:40])\n_, _, off_struct')
open('/tmp/f8ph.py','w').write(src)
print('fixed')
PYEOF
python3 /tmp/f8ph.py
