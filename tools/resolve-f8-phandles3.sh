#!/bin/sh
sudo -n python3 - < /dev/null 2>/dev/null || true
sudo -n sh -c 'cp /dev/stdin /tmp/run.sh' < /dev/null > /dev/null 2>&1 || true
# 直接通过 stdin 传 python 脚本执行：
sudo -n python3 - <<'PYEOF'
import struct
data = open('/sys/firmware/fdt','rb').read()
path = []
results = {}
structs_off = struct.unpack('>I', data[8:12])[0]
strings_off = struct.unpack('>I', data[16:20])[0]
p = structs_off
def get_string(off):
    e = data.index(b'\0', strings_off+off)
    return data[strings_off+off:e].decode()
while True:
    tok = struct.unpack('>I', data[p:p+4])[0]; p += 4
    if tok == 1:
        name = data[p:data.index(b'\0',p)].decode(); p = (p + len(name)+1+3)//4*4
        path.append(name)
    elif tok == 2:
        if path: path.pop()
    elif tok == 3:
        vlen, noff = struct.unpack('>II', data[p:p+8]); p += 8
        val = data[p:p+vlen]; p = (p + vlen + 3)//4*4
        pname = get_string(noff)
        if pname in ('linux,phandle','phandle') and vlen==4:
            results[struct.unpack('>I',val)[0]] = '/'+'/'.join(path)
    elif tok == 9:
        break
for ph in (485, 482, 479, 474, 478):
    print(ph, '->', results.get(ph, 'NOT-FOUND'))
PYEOF
echo DONE
