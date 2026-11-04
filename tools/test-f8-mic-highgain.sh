#!/bin/sh
# 提高捕获增益：PGA 拉满7 + Digital 满192 + ALC Stereo，录10秒验证语音电平
amixer -c 0 sset 'ALC Capture Function' Stereo >/dev/null
amixer -c 0 sset 'ALC Capture Max PGA' 7 >/dev/null
amixer -c 0 sset 'ALC Capture Min PGA' 0 >/dev/null
amixer -c 0 sset 'Capture Digital' 192 >/dev/null
amixer -c 0 sset 'Capture Mute' off >/dev/null
echo RECORDING_START
timeout 15 arecord -D hw:0,0 -f S16_LE -r 48000 -c 2 -d 10 /tmp/f8-gain.wav 2>&1 | tail -1
python3 - <<'PY'
import wave, struct
w = wave.open('/tmp/f8-gain.wav')
n = w.getnframes(); data = w.readframes(n)
s = struct.unpack('<%dh' % (len(data)//2), data)
seg = len(s)//10
peak = 0
for i in range(10):
    c = s[i*seg:(i+1)*seg]
    r = (sum(x*x for x in c)/len(c))**0.5
    peak = max(peak, r)
    print('sec%d-%d rms %.0f' % (i, i+1, r))
print('peak', max(abs(x) for x in s))
PY
echo DONE
