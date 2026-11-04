#!/bin/bash
# raw 在设备 /tmp，PGM 也在设备上生成
ssh -T -i /var/tmp/f8-pro-archlinux-20261027/private-keys/f8-pro-test-ed25519 \
  -o BatchMode=yes -o IdentitiesOnly=yes -o StrictHostKeyChecking=yes \
  -o UserKnownHostsFile=/var/tmp/f8-pro-archlinux-20261027/test-known-hosts \
  f8test@192.168.1.227 "sudo -n python3 - << 'PYEOF'
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
PYEOF"
echo MARKER_DONE
