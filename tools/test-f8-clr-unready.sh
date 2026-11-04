#!/bin/sh
echo "=== rkcif module params ==="
ls /sys/module/rkcif/parameters/ 2>/dev/null
echo "=== trigger clr_unready_dev (官方设计的 sensor 后加载恢复机制) ==="
echo 1 | sudo -n tee /sys/module/rkcif/parameters/clr_unready_dev 2>&1
sleep 3
echo "=== 之后 media0 是否出现 sensor ==="
sudo -n media-ctl -d /dev/media0 -p 2>/dev/null | grep -iE 'gc5035|ov8858' | head -4
echo "=== video0 现在能 open 吗 ==="
python3 -c "
import os
try:
    fd = os.open('/dev/video0', os.O_RDWR)
    print('video0 OPEN OK')
    os.close(fd)
except OSError as e:
    print('video0 fail:', e)
"
echo MARKER_DONE
