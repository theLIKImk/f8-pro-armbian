#!/bin/sh
export XDG_RUNTIME_DIR=/run/user/1601
sleep 2
pactl list sources short 2>&1
echo "---"
wpctl status 2>/dev/null | sed -n '/Sources/,/Filters/p'
echo DONE
