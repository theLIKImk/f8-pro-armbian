#!/bin/sh
# 打开捕获链路：ALC Stereo + PGA 增益 + 数字增益，然后录 3 秒看是否有过零数据
amixer -c 0 sset 'ALC Capture Function' Stereo >/dev/null
amixer -c 0 sset 'ALC Capture Max PGA' 7 >/dev/null
amixer -c 0 sset 'ALC Capture Min PGA' 0 >/dev/null
amixer -c 0 sset 'Capture Digital' 192 >/dev/null
amixer -c 0 sset 'Capture Mute' off >/dev/null
amixer -c 0 sset 'Main Mic' on >/dev/null
amixer -c 0 sset 'Headset Mic' off >/dev/null
echo "=== 录 3 秒 48k 单声道 ==="
timeout 8 arecord -D hw:0,0 -f S16_LE -r 48000 -c 2 -d 3 /tmp/f8-mic-test.wav 2>&1
ls -la /tmp/f8-mic-test.wav
python3 - <<'PY'
import wave, audioop
w = wave.open('/tmp/f8-mic-test.wav')
n = w.getnframes(); data = w.readframes(n)
print('frames', n, 'rms', audioop.rms(data, 2), 'max', audioop.max(data, 2))
PY
echo DONE
