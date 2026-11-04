#!/bin/bash
H=/var/tmp/f8-pro-armbian/official-kernel/usr/src/linux-headers-6.1.115-vendor-rk35xx
echo "media/i2c:"
ls "$H/drivers/media/i2c/" 2>/dev/null | head -8
echo "scripts count:"
ls "$H/scripts/" 2>/dev/null | wc -l
echo "Module.symvers:"
ls -la "$H/Module.symvers" 2>/dev/null || echo MISSING
echo MARKER_DONE
