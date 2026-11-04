#!/bin/sh
# 10 秒录音，用户在第 3-8 秒之间持续说话，分段对比有话/无话
echo "RECORDING_START"
timeout 15 arecord -D hw:0,0 -f S16_LE -r 48000 -c 2 -d 10 /tmp/f8-sync.wav 2>&1 | tail -1
python3 - <<'PY'
import wave, struct
w = wave.open('/tmp/f8-sync.wav')
n = w.getnframes(); data = w.readframes(n)
s = struct.unpack('<%dh' % (len(data)//2), data)
seg = len(s)//10
mx = 0
for i in range(10):
    c = s[i*seg:(i+1)*seg]
    r = (sum(x*x for x in c)/len(c))**0.5
    mx = max(mx, r)
    print('sec%d-%d rms %.0f' % (i, i+1, r))
print('peak', max(abs(x) for x in s))
print('VERDICT', 'VOICE_DETECTED' if mx > 3000 else 'NO_VOICE')
PY
rm -f /tmp/f8-sync.wav /tmp/f8-usertest.wav
echo DONE
