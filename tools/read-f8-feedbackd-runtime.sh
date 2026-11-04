#!/bin/sh
set -eu
export XDG_RUNTIME_DIR=/run/user/1601
export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1601/bus
/usr/libexec/feedbackd --help
gsettings list-recursively org.sigxcpu.feedbackd
getfacl -p /dev/input/event5
zcat /usr/share/man/man8/feedbackd.8.gz
