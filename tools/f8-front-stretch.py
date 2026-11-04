import struct, zlib

# 读取设备上的 PGM（10bit→8bit 提亮版）转 PNG，并做简单对比度拉伸让画面更可看
import sys

def read_pgm(path):
    with open(path, 'rb') as f:
        assert f.readline().strip() == b'P5'
        line = f.readline()
        while line.startswith(b'#'):
            line = f.readline()
        w, h = map(int, line.split())
        maxv = int(f.readline())
        data = f.read()
    return w, h, data

def write_png(path, w, h, gray):
    def chunk(t, d):
        c = struct.pack('>I', len(d)) + t + d
        return c + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)
    # 对比度拉伸：找 min/max
    mn = min(gray); mx = max(gray)
    rng = max(1, mx - mn)
    scaled = bytes(min(255, (v - mn) * 255 // rng) for v in gray)
    raw = b''.join(b'\x00' + scaled[y*w:(y+1)*w] for y in range(h))
    sig = b'\x89PNG\r\n\x1a\n'
    ihdr = chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 0, 0, 0, 0))
    idat = chunk(b'IDAT', zlib.compress(raw, 6))
    iend = chunk(b'IEND', b'')
    with open(path, 'wb') as f:
        f.write(sig + ihdr + idat + iend)

w, h, gray = read_pgm('/tmp/f8-front-preview.pgm')
write_png('/tmp/f8-front-stretch.png', w, h, gray)
print('stretch PNG saved', w, h, 'min/max used for stretch')
