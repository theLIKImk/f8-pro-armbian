#!/bin/sh
echo "=== video22 formats ==="
sudo -n v4l2-ctl -d /dev/video22 --list-formats-ext 2>&1 | head -14
echo "=== video31 formats ==="
sudo -n v4l2-ctl -d /dev/video31 --list-formats-ext 2>&1 | head -14
echo DONE
