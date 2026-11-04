#!/bin/sh
export XDG_RUNTIME_DIR=/run/user/1601
# 只有 sink。WP 没为 capture PCM 建 node。查 device 对象上 UCM profile 信息：
timeout 10 pw-cli ls Device > /tmp/f8-devs.txt 2>&1
grep -E 'device.name|api.alsa.*ucm|device.profile' /tmp/f8-devs.txt | head
echo "=== 找 card 设备的 profile 枚举 ==="
grep -A3 'alsa_card' /tmp/f8-devs.txt | head -20
echo DONE
