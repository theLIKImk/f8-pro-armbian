#!/bin/sh
export XDG_RUNTIME_DIR=/run/user/1601
timeout 8 pactl list sources short > /tmp/f8-sources.txt 2>&1
cat /tmp/f8-sources.txt
echo DONE
