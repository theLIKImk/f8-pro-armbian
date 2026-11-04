K=/lib/modules/6.1.115-vendor-rk35xx/kernel/drivers/media/i2c/gc5035.ko
sudo -n strings "$K" | grep -icE 'v4l2'
sudo -n strings "$K" | grep -icE 'subdev'
sudo -n modinfo gc5035 | grep -E 'vermagic|filename'
echo MARKER_DONE
