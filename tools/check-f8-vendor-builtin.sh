M=/var/tmp/f8-pro-armbian/official-kernel/lib/modules/6.1.115-vendor-rk35xx
grep -E 'gc5035|ov8858' "$M/modules.order" 2>/dev/null | head -2
echo M1
# vendor Image 内建清单：modules.builtin 里有没有 rkcif
grep -iE 'rkcif|rkisp|csi2-dphy' "$M/modules.builtin" 2>/dev/null | head -4
echo M2
