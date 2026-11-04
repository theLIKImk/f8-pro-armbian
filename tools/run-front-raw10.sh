#!/bin/bash
scp -i /var/tmp/f8-pro-archlinux-20261027/private-keys/f8-pro-test-ed25519 \
  -o BatchMode=yes -o IdentitiesOnly=yes \
  -o UserKnownHostsFile=/var/tmp/f8-pro-archlinux-20261027/test-known-hosts \
  /mnt/d/Netdisk/杂项/F8-PRO/archlinux/tools/f8-front-raw10.py \
  f8test@192.168.1.227:/tmp/f8-front-raw10.py
ssh -T -i /var/tmp/f8-pro-archlinux-20261027/private-keys/f8-pro-test-ed25519 \
  -o BatchMode=yes -o IdentitiesOnly=yes -o StrictHostKeyChecking=yes \
  -o UserKnownHostsFile=/var/tmp/f8-pro-archlinux-20261027/test-known-hosts \
  f8test@192.168.1.227 "sudo -n python3 /tmp/f8-front-raw10.py && sudo -n cp /tmp/f8-front-fixed.png /home/f8test/Pictures/F8Camera/front-fixed.png && sudo -n chown f8test:f8test /home/f8test/Pictures/F8Camera/front-fixed.png"
echo MARKER_DONE
