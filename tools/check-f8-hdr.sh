#!/bin/bash
HDR=/var/tmp/f8-pro-armbian/official-kernel/usr/src/linux-headers-6.1.115-vendor-rk35xx
echo "gc5035 files:"
ls "$HDR/drivers/media/i2c/" 2>/dev/null | grep -iE 'gc5035|ov8858'
echo "i2c Makefile:"
ls "$HDR/drivers/media/i2c/Makefile" 2>/dev/null
echo "scripts dir:"
ls "$HDR/scripts/" 2>/dev/null | head -5
echo "Module.symvers:"
ls "$HDR/Module.symvers" 2>/dev/null
echo MARKER_DONE
