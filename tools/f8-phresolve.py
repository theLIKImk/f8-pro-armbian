import struct
data = open('/tmp/c2.fdt','rb').read()
p = 0x38
end = 0x38 + 0x2a934
path = []
results = {}
eps = {}
node_props = {}
strings = 0x2a96c
def gs(off):
    e = data.index(b'\x00', strings+off)
    return data[strings+off:e].decode('latin1')
while p < end:
    tok = struct.unpack('>I', data[p:p+4])[0]; p += 4
    if tok == 1:
        name = data[p:data.index(b'\x00',p)].decode('latin1'); p = (p + len(name)+1+3)//4*4
        path.append(name)
    elif tok == 2:
        if path: path.pop()
    elif tok == 3:
        vlen, noff = struct.unpack('>II', data[p:p+8]); p += 8
        val = data[p:p+vlen]; p = (p + vlen + 3)//4*4
        pname = gs(noff)
        cp = '/'+'/'.join(path)
        node_props.setdefault(cp, {})[pname] = val
        if pname == 'phandle' and vlen == 4:
            results[struct.unpack('>I',val)[0]] = cp
        if pname == 'remote-endpoint' and vlen == 4:
            eps[cp] = struct.unpack('>I',val)[0]
# ===== 最终 C2 链路核对（// 键）=====
print('=== C2 DT 链路核对（本地构建树 FDT）===')
chain = [
    ('gc5035', '//i2c@fead0000/gc5035@37/port/endpoint'),
    ('dphy1-in', '//csi2-dphy1/ports/port@0/endpoint@1'),
    ('dphy1-out', '//csi2-dphy1/ports/port@1/endpoint@0'),
    ('mipi2-in', '//mipi2-csi2/ports/port@0/endpoint@1'),
    ('mipi2-out', '//mipi2-csi2/ports/port@1/endpoint@0'),
    ('cif2', '//rkcif-mipi-lvds2/port/endpoint'),
    ('sditf2', '//rkcif-mipi-lvds2-sditf/port/endpoint'),
    ('rkisp1', '//rkisp1-vir0/port/endpoint@0'),
    ('ov8858', '//i2c@fead0000/ov8858@36/port/endpoint'),
    ('dphy2-in', '//csi2-dphy2/ports/port@0/endpoint@1'),
    ('dphy2-out', '//csi2-dphy2/ports/port@1/endpoint@1'),
    ('mipi3-in', '//mipi3-csi2/ports/port@0/endpoint@1'),
    ('mipi3-out', '//mipi3-csi2/ports/port@1/endpoint@0'),
    ('cif3', '//rkcif-mipi-lvds3/port/endpoint'),
    ('sditf3', '//rkcif-mipi-lvds3-sditf/port/endpoint'),
    ('rkisp0', '//rkisp0-vir0/port/endpoint@0'),
]
ok = True
for name, node in chain:
    r = eps.get(node)
    tgt = results.get(r, 'NONE') if r else 'NO-REMOTE'
    print(f'{name}: -> {tgt}')
