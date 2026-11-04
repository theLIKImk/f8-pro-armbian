#!/bin/sh
sudo -n tee /usr/share/wireplumber/wireplumber.conf.d/50-f8-ucm.conf > /dev/null <<'EOF'
monitor.alsa.properties = {
  api.alsa.use-ucm = true
}
EOF
ls -la /usr/share/wireplumber/wireplumber.conf.d/
systemctl --user restart wireplumber
sleep 8
export XDG_RUNTIME_DIR=/run/user/1601
timeout 10 pw-cli ls Node 2>&1 | grep -E 'alsa_(output|input)|media.class = .Audio' | head -12
echo DONE
