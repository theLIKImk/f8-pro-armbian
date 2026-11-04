#!/bin/sh
export XDG_RUNTIME_DIR=/run/user/1601
# pw-dump 看 Audio/Sink 与 node 类型（比 pactl 更底层不挂）：
timeout 8 pw-cli ls Node 2>/dev/null | grep -E 'node.description|media.class' | head -20
echo DONE
