sudo -n python3 -c "
import os
try:
    fd = os.open('/dev/video0', os.O_RDWR)
    print('video0 opened fd', fd)
    os.close(fd)
except Exception as e:
    print('video0 open fail:', e)
"
sudo -n v4l2-ctl --list-devices 2>&1 | head -18
echo DONE
