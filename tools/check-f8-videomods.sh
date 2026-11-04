ls /lib/modules/6.1.115-vendor-rk35xx/kernel/drivers/media/ 2>/dev/null
echo ---
# rkcif/rkisp 在官方 Image 是内建还是模块（不在 lsmod 里说明内建）：
modinfo rkcif 2>/dev/null | head -2 || echo rkcif-not-a-module
modinfo rkisp 2>/dev/null | head -2 || echo rkisp-not-a-module
echo MARKER_DONE
