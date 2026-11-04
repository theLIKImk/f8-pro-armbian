#!/bin/sh
python3 - <<'PY'
import wave, struct
w = wave.open('/tmp/f8-mic-test.wav')
n = w.getnframes(); data = w.readframes(n)
samples = struct.unpack('<%dh' % (len(data)//2), data)
peak = max(abs(s) for s in samples)
rms = (sum(s*s for s in samples) / len(samples)) ** 0.5
print('frames', n, 'peak', peak, 'rms', round(rms,1))
PY
rm -f /tmp/f8-mic-test.wav
echo DONE
