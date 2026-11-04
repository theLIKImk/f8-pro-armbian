#!/bin/bash
cat > /tmp/f8pgm.py << 'PYEOF'
data = open('/tmp/f8-front-rg10.raw','rb').read()
W, H = 2592, 1944
stride = 3328
rows = []
for by in range(0, H, 4):
    row = bytearray()
    for bx in range(0, W, 4):
        s = 0; c = 0
        for y in (by, by+1):
            base = y*stride
            for x in (bx, bx+1):
                if base+x < len(data):
                    s += data[base+x]
                    c += 1
        row.append(min(255, (s//max(c,1))*2))
    rows.append(bytes(row))
with open('/tmp/f8-front-preview.pgm','wb') as f:
    f.write(b'P5\n%d %d\n255\n' % (W//4, H//4))
    for r in rows:
        f.write(r)
print('PGM saved', W//4, H//4)
PYEOF
sudo -n python3 /tmp/f8pgm.py
echo MARKER_DONE
