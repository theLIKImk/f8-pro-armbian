#!/bin/bash
scp -i /var/tmp/f8-pro-archlinux-20261027/private-keys/f8-pro-test-ed25519 \
  -o BatchMode=yes -o IdentitiesOnly=yes \
  -o UserKnownHostsFile=/var/tmp/f8-pro-archlinux-20261027/test-known-hosts \
  f8test@192.168.1.227:/home/f8test/Pictures/F8Camera/front-fixed.png \
  "/mnt/d/Netdisk/杂项/F8-PRO/archlinux/local/hardware/camera-c4-frames/f8-front-fixed.png"
echo MARKER_DONE
