#!/bin/sh
# 增益已在最大(数字192/PGA7)，但语音RMS仍~1000-2000，与之前PGA3时几乎相同！
# 增益不影响电平 => 信号在进入PGA前就被衰减，或者ADC数据选择/路径不对。
# 检查：ADC Data Select 当前 'Left Right'，及模拟前端 "Left/Right Channel" (0-8)！
# 之前看到 'Left Channel'/'Right Channel' 是 capture volume 0-8 且为 0 —— 这才是真正的模拟增益！
echo "=== Left/Right Channel capture volume (0-8) ==="
amixer -c 0 sget 'Left Channel'
amixer -c 0 sget 'Right Channel'
echo "=== 设为最大 8 再录 ==="
amixer -c 0 sset 'Left Channel' 8 >/dev/null
amixer -c 0 sset 'Right Channel' 8 >/dev/null
amixer -c 0 sset 'ALC Capture Function' Stereo >/dev/null
amixer -c 0 sset 'ALC Capture Max PGA' 7 >/dev/null
amixer -c 0 sset 'Capture Digital' 192 >/dev/null
echo RECORDING_START
timeout 15 arecord -D hw:0,0 -f S16_LE -r 48000 -c 2 -d 10 /tmp/f8-gain2.wav 2>&1 | tail -1
python3 - <<'PY'
import wave, struct
w = wave.open('/tmp/f8-gain2.wav')
n = w.getnframes(); data = w.readframes(n)
s = struct.unpack('<%dh' % (len(data)//2), data)
seg = len(s)//10
for i in range(10):
    c = s[i*seg:(i+1)*seg]
    print('sec%d-%d rms %.0f' % (i, i+1, (sum(x*x for x in c)/len(c))**0.5))
print('peak', max(abs(x) for x in s))
PY
rm -f /tmp/f8-gain.wav /tmp/f8-gain2.wav
echo DONE
