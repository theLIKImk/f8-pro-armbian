#!/bin/sh
# seg0(12387)+削波是开始瞬间的爆音；之后本底 7-15 无语音输入。
# 请你在录音期间对着平板说话/敲屏幕附近，验证麦克风是否有实际声音进入。
# 为准同时测两个输入选择：Line1(可能是 headset)与 Differential：
amixer -c 0 sset 'Left PGA Mux' 'Line 1L' >/dev/null
amixer -c 0 sset 'Right PGA Mux' 'Line 1R' >/dev/null
timeout 10 arecord -D hw:0,0 -f S16_LE -r 48000 -c 2 -d 5 /tmp/f8-mic5.wav 2>&1 | tail -1
python3 - <<'PY'
import wave, struct
w = wave.open('/tmp/f8-mic5.wav')
n = w.getnframes(); data = w.readframes(n)
s = struct.unpack('<%dh' % (len(data)//2), data)
seg = len(s)//10
print('LINE1 mux:')
for i in range(10):
    c = s[i*seg:(i+1)*seg]
    print('seg%d rms %.0f' % (i, (sum(x*x for x in c)/len(c))**0.5))
print('peak', max(abs(x) for x in s))
PY
amixer -c 0 sset 'Left PGA Mux' 'DifferentialL' >/dev/null
amixer -c 0 sset 'Right PGA Mux' 'DifferentialR' >/dev/null
rm -f /tmp/f8-mic5.wav
echo DONE
