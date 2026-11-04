#!/bin/sh
# WirePlumber 还没创建 capture source —— profile 可能只有输出。查 card profile：
pactl list cards | grep -E 'Profiles:|Active Profile' -A8 | head -20
echo ---
wpctl status 2>/dev/null | grep -A10 Audio | head -20
echo DONE
