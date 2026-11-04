#!/bin/sh
set -eu
if [ -f /etc/f8-pro-native-desktop-t1 ]; then
    /bin/sh /usr/libexec/f8-pro/native-prepare.sh
else
    /bin/sh /usr/libexec/f8-pro/live-setup.sh
fi
getent group nopasswdlogin >/dev/null || groupadd -r nopasswdlogin
usermod -a -G video,render,nopasswdlogin f8test
echo 'F8 DESKTOP: test user and input-method defaults ready'
