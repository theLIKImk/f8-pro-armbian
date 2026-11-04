sudo -n python3 -c "
import os, glob
for d in sorted(glob.glob('/dev/video*')):
    try:
        fd = os.open(d, os.O_RDWR)
        os.close(fd)
    except OSError as e:
        print(d, e.errno, e)
" 2>&1 | head -25
echo DONE
