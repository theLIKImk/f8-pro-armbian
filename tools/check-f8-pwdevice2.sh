#!/bin/sh
export XDG_RUNTIME_DIR=/run/user/1601
timeout 10 pw-cli ls Device 2>&1 | head -60
echo DONE
