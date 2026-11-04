ls /lib/modules/6.1.115-vendor-rk35xx/kernel/drivers/media/platform/ 2>/dev/null | head -10
echo ---
modinfo rkcif 2>&1 | head -2
echo ---
# 官方 Image 里 rkcif 在哪：
find /lib/modules/6.1.115-vendor-rk35xx -name 'rkcif*' -o -name 'rkisp*' 2>/dev/null | head -5
echo MARKER_DONE
