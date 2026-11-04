#!/bin/sh
ls /usr/src/linux-headers-6.1.115-vendor-rk35xx/drivers/power/supply/ | grep -iE 'cw|bat'
echo "---c files count:"
ls /usr/src/linux-headers-6.1.115-vendor-rk35xx/drivers/power/supply/*.c 2>/dev/null | wc -l
echo DONE
