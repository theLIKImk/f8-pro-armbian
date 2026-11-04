#!/bin/sh
echo "=== 捕获设备 ==="
arecord -l 2>&1
arecord -L 2>/dev/null | head -20
echo "=== 声卡 Mixer 捕获控制 ==="
amixer -c 0 scontrols 2>/dev/null | grep -iE 'capture|adc|mic|record'
echo "=== 关键捕获控制值 ==="
for c in "Capture Mute" "Capture Digital" "ALC Capture Function" "ALC Capture Max PGA" "Main Mic" "Headset Mic" "ADC Data Select" "Left PGA Mux" "Right PGA Mux"; do
  echo "-- $c"; amixer -c 0 sget "$c" 2>/dev/null | grep -v '^$' | head -6
done
echo "=== PipeWire sources ==="
pactl list sources short 2>/dev/null
echo "=== DAI / card info ==="
cat /proc/asound/card0/pcm0c/info 2>/dev/null
echo DONE
