#!/bin/bash
H=/var/tmp/f8-pro-armbian/official-kernel/usr/src/linux-headers-6.1.115-vendor-rk35xx
ls "$H/drivers/media/i2c/" | wc -l
ls "$H/drivers/media/i2c/"*.c 2>/dev/null | wc -l
find "$H/drivers/media/i2c" -name 'gc5035*' -o -name 'ov8858*' | head -4
ls "$H/drivers/media/i2c/Makefile" 2>/dev/null && echo HAS_MK
echo MARKER_DONE
