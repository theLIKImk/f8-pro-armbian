#!/bin/sh
# 把前摄预览 PGM 转 PNG 拷到用户桌面，方便直接查看
sudo -n cp /tmp/f8-front-preview.pgm /home/f8test/Pictures/F8Camera/front-preview.pgm
sudo -n chown f8test:f8test /home/f8test/Pictures/F8Camera/front-preview.pgm
ls -la /home/f8test/Pictures/F8Camera/
echo MARKER_DONE
