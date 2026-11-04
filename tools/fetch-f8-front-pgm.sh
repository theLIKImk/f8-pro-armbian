#!/bin/bash
# 把 PGM 拷回 Windows 供用户查看
scp -i /var/tmp/f8-pro-archlinux-20261027/private-keys/f8-pro-test-ed25519 \
  -o BatchMode=yes -o IdentitiesOnly=yes \
  -o UserKnownHostsFile=/var/tmp/f8-pro-archlinux-20261027/test-known-hosts \
  f8test@192.168.1.227:/tmp/f8-front-preview.pgm \
  '/mnt/d/Netdisk/杂项/F8-PRO/archlinux/local/hardware/camera-c4-frames/f8-front-preview.pgm'
ls -la '/mnt/d/Netdisk/杂项/F8-PRO/archlinux/local/hardware/camera-c4-frames/f8-front-preview.pgm'
echo MARKER_DONE
