#!/bin/sh
# 疑问1：spk switch=false 但 Speaker(on)？可能 alsactl 恢复顺序里 'Speaker Switch' 和
# 'spk switch' 是不同控件。检查两者：
echo "--- state file values:"
grep -A2 "name 'spk switch'" /var/lib/alsa/asound.state | grep value
grep -A2 "name 'Speaker Switch'" /var/lib/alsa/asound.state | grep value
grep -A2 "name 'OUT2 Switch'" /var/lib/alsa/asound.state | grep value
echo "--- live:"
amixer -c 0 sget 'spk switch' | grep Mono
amixer -c 0 sget 'Speaker' | grep Mono
amixer -c 0 sget 'OUT2' | grep Mono
echo "--- store spk switch true (target):"
amixer -c 0 sset 'spk switch' on
amixer -c 0 sset 'Speaker' on
alsactl store 0 -f /tmp/f8-test2.state 2>&1 | head -1
grep -A2 "name 'spk switch'" /tmp/f8-test2.state | grep value
echo DONE
