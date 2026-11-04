import struct
data = open('/tmp/c2.fdt','rb').read()
p = 0x38
end = 0x38 + 0x2a934
strings = 0x2a96c
path = []
nodes = {}   # path -> props
children = {}  # path -> [child names]
def gs(off):
    e = data.index(b'\x00', strings+off)
    return data[strings+off:e].decode('latin1')
cur_children = []
while p < end:
    tok = struct.unpack('>I', data[p:p+4])[0]; p += 4
    if tok == 1:
        name = data[p:data.index(b'\x00',p)].decode('latin1'); p = (p + len(name)+1+3)//4*4
        path.append(name)
        cur_children = []
    elif tok == 2:
        n = '/' + '/'.join(path)
        nodes[n] = nodes.get(n, {})
        if path: path.pop()
    elif tok == 3:
        vlen, noff = struct.unpack('>II', data[p:p+8]); p += 8
        val = data[p:p+vlen]; p = (p + vlen + 3)//4*4
        pname = gs(noff)
        n = '/' + '/'.join(path)
        nodes.setdefault(n, {})[pname] = val
    elif tok == 9:
        break

# rkcif-mipi-lvds2 的子图：node 自身有 port/endpoint 吗？
lvds2 = '/rkcif-mipi-lvds2'
sub = [k for k in nodes if k.startswith(lvds2)]
print('rkcif-mipi-lvds2 subtree:')
for s in sub:
    print(' ', s, sorted(nodes[s].keys()))
print()
print('关键：v4l2_async_nf_parse_fwnode_endpoints 遍历 rkcif-mipi-lvds2 节点的')
print('graph endpoints（fwnode_graph_for_each_endpoint）。C2 的 lvds2 有 port/endpoint，')
print('其 remote 指向 mipi2-csi2 port@1 —— 所以 rkcif notifier 的 asd fwnode = ')
print('mipi2-csi2 的 endpoint（作为 remote）。匹配对象 = 注册进 async 的 subdev，')
print('其 fwnode 是 mipi2-csi2 的 endpoint —— 即 mipi-csi2 驱动的 subdev！')
print('mipi-csi2 驱动注册 subdev 用的 fwnode 是它自己 dev 节点，不是 endpoint ——')
print('但 heterogeneous 匹配（endpoint vs device）会取 port parent 比较 = mipi2-csi2 节点 == mipi2-csi2 节点，应匹配！')
