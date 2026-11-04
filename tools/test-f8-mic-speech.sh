#!/bin/sh
# 静音环境 rms 167 属本底噪声，正常。峰值未削波。
# 现在录一段 5 秒，请用户对着平板说话，我来分析动态：
timeout 10 arecord -D hw:0,0 -f S16_LE -r 48000 -c 2 -d 5 /tmp/f8-mic3.wav 2>&1 | tail -1
python3 - <<'PY'
import wave, struct
w = wave.open('/tmp/f8-mic3.wav')
n = w.getnframes(); data = w.readframes(n)
s = struct.unpack('<%dh' % (len(data)//2), data)
# 分 10 段看每段 rms
seg = len(s)//10
for i in range(10):
    c = s[i*seg:(i+1)*seg]
    r = (sum(x*x for x in c)/len(c))**0.5
    print('seg%d rms %.0f' % (i, r))
print('peak', max(abs(x) for x in s))
PY
rm -f /tmp/f8-mic2.wav /tmp/f8-mic3.wav
echo DONE
