#!/bin/sh
export XDG_RUNTIME_DIR=/run/user/1601
# pw-dump 空输出——可能挂在 registry。换 pw-cli ls Node 逐个看（输出直接落盘）：
timeout 10 pw-cli ls Node > /tmp/f8-nodes.txt 2>&1
grep -c 'id:' /tmp/f8-nodes.txt
grep -B2 -A2 'media.class' /tmp/f8-nodes.txt | grep -E 'Audio|node.name' | head -20
echo DONE
