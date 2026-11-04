import struct, zlib

# 正确解析 MIPI RAW10 packed：每 5 字节含 4 像素
# byte[0..3] = p0..p3 低8位, byte[4] 高2位: [p3h p2h p1h p0h]
data = open('/tmp/f8-front-rg10.raw','rb').read()
W, H = 2592, 1944
stride = 3328   # 3240 packed bytes + 88 padding

def unpack_row(y):
    """解一行 packed RAW10，返回 W 个 10bit 值"""
    base = y * stride
    row = []
    for x0 in range(0, W, 4):
        o = base + (x0 // 4) * 5
        b0, b1, b2, b3, b4 = data[o], data[o+1], data[o+2], data[o+3], data[o+4]
        row.append(b0 | ((b4 & 0x03) << 8))
        row.append(b1 | ((b4 & 0x0C) << 6))
        row.append(b2 | ((b4 & 0x30) << 4))
        row.append(b3 | ((b4 & 0xC0) << 2))
    return row

# 只解偶数行（RGGB 隔行），做 2x2 降采样到 648x486
out_w, out_h = W // 4, H // 4
gray = []
for by in range(0, H, 4):
    r0 = unpack_row(by)
    r1 = unpack_row(by + 1)
    row = bytearray()
    for bx in range(0, W, 4):
        # RGGB: r0[bx]=R r0[bx+1]=Gr r1[bx]=Gb r1[bx+1]=B
        r = r0[bx]; g = (r0[bx+1] + r1[bx]) // 2; b = r1[bx+1]
        v = (r * 299 + g * 587 + b * 114) // 1000
        row.append(min(255, v >> 2))   # 10bit → 8bit
    gray.append(row)

# 写灰度 PGM
with open('/tmp/f8-front-fixed.pgm', 'wb') as f:
    f.write(b'P5\n%d %d\n255\n' % (out_w, out_h))
    for r in gray:
        f.write(bytes(r))

# 对比度拉伸 + 写 PNG
mn = min(min(r) for r in gray)
mx = max(max(r) for r in gray)
rng = max(1, mx - mn)
def write_png(path, w, h, rows):
    def chunk(t, d):
        c = struct.pack('>I', len(d)) + t + d
        return c + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)
    scaled_rows = [bytes(min(255, (v - mn) * 255 // rng) for v in r) for r in rows]
    raw = b''.join(b'\x00' + r for r in scaled_rows)
    sig = b'\x89PNG\r\n\x1a\n'
    ihdr = chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 0, 0, 0, 0))
    idat = chunk(b'IDAT', zlib.compress(raw, 6))
    with open(path, 'wb') as f:
        f.write(sig + ihdr + idat + chunk(b'IEND', b''))

write_png('/tmp/f8-front-fixed.png', out_w, out_h, gray)
print('fixed PNG saved', out_w, out_h, 'dynamic range:', mn, '-', mx)
