#!/bin/sh
echo "=== video_rkcif params ==="
ls /sys/module/video_rkcif/parameters/ 2>/dev/null
echo "=== trigger ==="
echo 1 | sudo -n tee /sys/module/video_rkcif/parameters/clr_unready_dev 2>&1
sleep 3
echo "=== media0 sensor? ==="
sudo -n media-ctl -d /dev/media0 -p 2>/dev/null | grep -icE 'gc5035|ov8858'
echo "=== video0 open? ==="
sudo -n python3 -c "
import os
try:
    fd = os.open('/dev/video0', os.O_RDWR); print('video0 OPEN OK'); os.close(fd)
except OSError as e:
    print('video0 fail:', e)
"
echo MARKER_DONE
