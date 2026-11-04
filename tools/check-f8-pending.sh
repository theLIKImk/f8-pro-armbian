#!/bin/sh
sudo -n cat /sys/kernel/debug/v4l2-async/pending_async_subdevices 2>/dev/null
echo MARKER_DONE
