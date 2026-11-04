#!/bin/sh
amixer -c 0 sset 'ALC Capture Function' Stereo >/dev/null
amixer -c 0 sset 'ALC Capture Max PGA' 7 >/dev/null
amixer -c 0 sset 'Capture Digital' 192 >/dev/null
timeout 10 arecord -D hw:0,0 -f S16_LE -r 48000 -c 2 -d 5 /tmp/f8-usertest.wav 2>&1 | tail -1
python3 - <<'PY'
import wave, struct
w = wave.open('/tmp/f8-usertest.wav')
n = w.getnframes(); data = w.readframes(n)
s = struct.unpack('<%dh' % (len(data)//2), data)
seg = len(s)//10
for i in range(10):
    c = s[i*seg:(i+1)*seg]
    print('seg%d rms %.0f' % (i, (sum(x*x for x in c)/len(c))**0.5))
print('peak', max(abs(x) for x in s))
PY
echo DONE
