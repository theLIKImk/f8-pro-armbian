#!/bin/sh
export XDG_RUNTIME_DIR=/run/user/1601
# device.path = alsa:acp:... —— WP 用的是 ACP（alsa-card-profiles）而不是 UCM！
# ACP 模式下 capture profile 需要内核 PCM 枚举；pcm0c 存在。ACP 为什么没建输入？
# 可能 ACP 的 profile 枚举把双向 PCM 只当 playback（dailink 双向同一 PCM）。
# 试试强制 WP 用 UCM 而非 ACP：
ls /etc/wireplumber/ 2>/dev/null
sudo -n mkdir -p /etc/wireplumber
sudo -n tee /etc/wireplumber/config.lua.d/50-f8-ucm.lua > /dev/null <<'EOF'
alsa_monitor.properties = {
  ["api.alsa.use-ucm"] = true,
}
EOF
systemctl --user restart wireplumber
sleep 8
timeout 10 pw-cli ls Node 2>&1 | grep -E 'node.name.*alsa|media.class' | head -12
echo DONE
