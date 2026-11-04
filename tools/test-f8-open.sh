#!/bin/sh
# /dev/video0 minor 81:0 与 sysfs 81:0 一致 —— 节点存在。之前 v4l2-ctl 打不开
# 是因为 ls -la 行缺失？再直接试 open：
sudo -n python3 -c "
import os
try:
    fd = os.open('/dev/video0', os.O_RDWR)
    print('video0 opened fd', fd)
    os.close(fd)
except Exception as e:
    print('video0 open fail:', e)
"
echo "---"
sudo -n v4l2-ctl --list-devices 2>&1 | head -20
echo DONE
