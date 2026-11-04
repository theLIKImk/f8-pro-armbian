#!/bin/sh
# peak 32768 = 削波(饱和)！信号强但 PGA 全开导致失真。
# 找到合适增益：逐步降低 ALC/数字增益，录 2 秒，说话时 RMS 目标 1000-8000、不削波。
amixer -c 0 sset 'ALC Capture Function' Off >/dev/null
amixer -c 0 sset 'ALC Capture Max PGA' 3 >/dev/null
amixer -c 0 sset 'Capture Digital' 128 >/dev/null
timeout 6 arecord -D hw:0,0 -f S16_LE -r 48000 -c 2 -d 2 /tmp/f8-mic2.wav 2>&1 | tail -1
python3 - <<'PY'
import wave, struct
w = wave.open('/tmp/f8-mic2.wav')
n = w.getnframes(); data = w.readframes(n)
s = struct.unpack('<%dh' % (len(data)//2), data)
print('ALC off PGA3 dig128: peak', max(abs(x) for x in s), 'rms', round((sum(x*x for x in s)/len(s))**0.5,1))
PY
echo DONE
