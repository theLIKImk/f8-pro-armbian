#!/bin/sh
# 段0有声音(334,残余开启瞬间)，之后全静音(rms 1)——捕获通道被系统在运行后 mute 或 DAPM 关闭。
# 对比：第一段(ALC on, PGA7)有连续数据(rms 3597)。怀疑 PGA/ALC 下的路径才是活的，
# 但更可能是PipeWire挂起或者DAPM: 重新 ALC Stereo + PGA 3 再录：
amixer -c 0 sset 'ALC Capture Function' Stereo >/dev/null
amixer -c 0 sset 'ALC Capture Max PGA' 3 >/dev/null
amixer -c 0 sset 'ALC Capture Min PGA' 0 >/dev/null
amixer -c 0 sset 'Capture Digital' 192 >/dev/null
timeout 10 arecord -D hw:0,0 -f S16_LE -r 48000 -c 2 -d 5 /tmp/f8-mic4.wav 2>&1 | tail -1
python3 - <<'PY'
import wave, struct
w = wave.open('/tmp/f8-mic4.wav')
n = w.getnframes(); data = w.readframes(n)
s = struct.unpack('<%dh' % (len(data)//2), data)
seg = len(s)//10
for i in range(10):
    c = s[i*seg:(i+1)*seg]
    print('seg%d rms %.0f' % (i, (sum(x*x for x in c)/len(c))**0.5))
print('peak', max(abs(x) for x in s))
PY
rm -f /tmp/f8-mic4.wav
echo DONE
