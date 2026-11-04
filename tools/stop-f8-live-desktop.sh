#!/bin/sh
set -eu
systemctl stop sddm.service
systemctl start f8-live-status.service
chvt 2
