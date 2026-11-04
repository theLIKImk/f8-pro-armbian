#!/bin/sh
export XDG_RUNTIME_DIR=/run/user/1601
# PW daemon 可能没真正起来。检查：
systemctl --user status pipewire --no-pager -n 3 | head -6
ls /run/user/1601/ | grep -i pipe
timeout 5 pw-cli info 0 2>&1 | head -3
echo DONE
