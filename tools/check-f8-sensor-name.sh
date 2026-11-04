sudo -n dmesg | grep -iE 'async register subdev failed|subdev failed|entity' | grep -iE 'gc5035|ov8858|m00|m01' | head -6
echo M1
# 关键：subdev name 格式 m00_gc5035 — — 找这个名字：
sudo -n dmesg | grep -E 'm0[01]_' | head -5
echo MARKER_DONE
