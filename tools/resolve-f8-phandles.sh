#!/bin/sh
# 关键线索拼图：
# - gc5035 endpoint remote = 485
# - ov8858 endpoint remote = 482
# - dphy1 port0 endpoint@1 remote = 479（应指向 sensor！）
# - dphy2 port0 endpoint@1 remote = 474
# remote 值互不匹配 = 双向断链！sensor 指向 485/482，dphy 指向 479/474。
# 485/482/479/474 分别是哪些 endpoint？可能 DT 里 sensor→dphy 之间有 mipi 端点
# 层级错位（C2 改动后 phandle 重排）。
# 用 python 直接解析 fdt 找这些 phandle 节点路径：
sudo -n python3 - <<'PYEOF'
import struct
data = open('/sys/firmware/fdt','rb').read()
# 简单 fdt 解析：找所有 linux,phandle 属性与其所在节点路径
pos = 0
tokens = {1:'BEGIN_NODE',2:'END_NODE',3:'PROP',4:'NOP',9:'END'}
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
