#!/bin/sh
export XDG_RUNTIME_DIR=/run/user/1601
sleep 3
timeout 12 pw-cli ls Node 2>&1 | grep -B4 'media.class = "Audio/Source"' | head -10
echo "--- all alsa nodes:"
timeout 12 pw-cli ls Node 2>&1 | grep 'node.name' | grep alsa
echo DONE
