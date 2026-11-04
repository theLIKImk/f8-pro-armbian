#!/bin/sh
set -eu
gst-inspect-1.0 v4l2deviceprovider
printenv | sort | sed -n '/^GST_/p'
ls -l /dev/v4l/by-path/
