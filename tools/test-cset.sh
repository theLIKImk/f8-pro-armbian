#!/bin/sh
# cset 失败但控件存在。可能因为 UCM EnableSequence 的 cset 需要 numid 或
# 是在另一 mixer 设备上。直接验证：手工执行同样 cset：
amixer -c 0 cset name='Main Mic' on 2>&1 | tail -1
amixer -c 0 cset name='Left Channel Capture Volume' 8 2>&1 | tail -1
echo "rc=$?"
echo DONE
