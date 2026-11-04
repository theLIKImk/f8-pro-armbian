#!/bin/sh
# 把 NV12 帧转 PNG 供用户查看（用 ffmpeg 或 python）
which ffmpeg >/dev/null 2>&1 && {
  ffmpeg -y -loglevel error -f rawvideo -pix_fmt nv12 -s 640x480 -i /tmp/f8-front-a.raw \
    -frames:v 1 /tmp/f8-front-a.png 2>&1
  echo ffmpeg-ok
} || echo no-ffmpeg
ls -la /tmp/f8-front-a.png 2>/dev/null
# 计算平均亮度判断曝光是否合适
python3 - << 'PYEOF'
import struct
data = open('/tmp/f8-front-a.raw','rb').read()
# NV12: Y plane 640*480=307200 bytes
y = data[:307200]
avg = sum(y)/len(y)
mx = max(y); mn = min(y)
print('Y avg=%.1f min=%d max=%d' % (avg, mn, mx))
print('exposure judge:', 'too dark' if avg < 40 else 'too bright' if avg > 220 else 'acceptable')
PYEOF
echo MARKER_DONE
