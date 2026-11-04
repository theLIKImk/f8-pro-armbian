#!/bin/sh
# PCM=166 set 疑被 PipeWire 恢复覆盖，且 store 在 WP 环境下不持久？
# 直接检查：set 是否生效
amixer -c 0 sset 'PCM' 166 2>&1 | tail -2
echo "--- live:"
amixer -c 0 sget 'PCM' | grep 'Front Left'
echo "--- store verbose:"
alsactl store 0 -f /tmp/f8-test.state 2>&1 | head -2
grep -A3 "name 'PCM Volume'" /tmp/f8-test.state | grep 'value\.'
echo "--- spk switch live (was false in state, but live showed on?):"
amixer -c 0 sget 'spk switch' | grep Mono
amixer -c 0 sget 'Speaker' | grep Mono
