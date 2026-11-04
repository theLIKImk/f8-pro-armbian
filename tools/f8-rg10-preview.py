#!/bin/bash
# 把 RG10 raw 转 PNG 供用户查看（软件 debayer 简化版：RGGB → 灰度/简单插值）
# RG10: 10-bit packed? 按 C4 记录 bytes/line=3328 for 2592px → 3328*8/2592≈10.27 → 是 10bit 保存在 16bit 容器（MIPI RAW10 解包后）
# 3328/2=1664 u16 per line… 2592 不整除。实际 MIPI RAW10 packed: 4px in 5 bytes → 2592*10/8=3240B? 但记录 3328 → 可能含填充。
# 稳妥：按宽3328字节处理，取每字节低8位近似（丢失2位精度可接受预览）
python3 - << 'PYEOF'
data = open('/tmp/f8-front-rg10.raw','rb').read()
W, H = 2592, 1944
stride = 3328
# RGGB: R G / Gr B —— 2x2 block
# 简单预览：缩略到 648x486（每4像素取1块平均），输出灰度 PGM → PNG 需要库；直接输出 PGM(P5) 用户可看
import sys
out_w, out_h = W//4, H//4
rows = []
for by in range(0, H, 4):
    row = bytearray()
    for bx in range(0, W, 4):
        # 取该 4x4 块的 4 通道均值（近似亮度）
        s = 0; c = 0
        for y in (by, by+1):
            base = y*stride
            for x in (bx, bx+1):
                if base+x < len(data):
                    s += data[base+x] << 2   # 8bit→10bit 近似（实际是10bit高位在低8位？按C4成功记录为准）
                    c += 1
        row.append(min(255, s//max(c,1)))
    rows.append(bytes(row))
with open('/tmp/f8-front-preview.pgm','wb') as f:
    f.write(b'P5\n%d %d\n255\n' % (out_w, out_h))
    for r in rows: f.write(r)
print('PGM saved', out_w, out_h)
PYEOF
ls -la /tmp/f8-front-preview.pgm
echo MARKER_DONE
