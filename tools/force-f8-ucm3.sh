#!/bin/sh
# alsa.lua 默认 api.alsa.use-acp=true —— ACP 模式。ACP 枚举不到 capture profile。
# UCM 强制需要 use-acp=false + use-ucm=true。更新配置：
sudo -n tee /usr/share/wireplumber/wireplumber.conf.d/50-f8-ucm.conf > /dev/null <<'EOF'
monitor.alsa.properties = {
  api.alsa.use-acp = false
  api.alsa.use-ucm = true
}
EOF
systemctl --user restart wireplumber pipewire
sleep 8
export XDG_RUNTIME_DIR=/run/user/1601
timeout 12 pw-cli ls Node 2>&1 | grep 'node.name' | grep -i alsa
echo DONE
