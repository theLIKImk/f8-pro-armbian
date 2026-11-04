#!/bin/sh
export XDG_RUNTIME_DIR=/run/user/1601
echo "=== source 状态 ==="
wpctl status 2>/dev/null | sed -n '/Sources/,/Filters/p'
echo "=== 录 10 秒，请持续说话 ==="
timeout 15 pw-record --target alsa_input.platform-es8388-sound.HiFi__Mic__source /tmp/f8-final.wav 2>&1 &
REC=$!
sleep 11
kill $REC 2>/dev/null
ls -la /tmp/f8-final.wav
python3 - <<'PY'
import wave, struct
try:
    w = wave.open('/tmp/f8-final.wav')
    n = w.getnframes(); data = w.readframes(n)
    s = struct.unpack('<%dh' % (len(data)//2), data)
    seg = len(s)//8
    for i in range(8):
        c = s[i*seg:(i+1)*seg]
        print('seg%d rms %.0f' % (i, (sum(x*x for x in c)/len(c))**0.5))
    print('peak', max(abs(x) for x in s))
except Exception as e:
    print('parse err', e)
PY
echo DONE
