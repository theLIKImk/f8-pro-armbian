#!/bin/sh
# 用项目自带的 f8_resource_image.py 重建 resource.img（新 DTB + 原 logo）：
set -e
SRC=/var/tmp/f8-pro-armbian/native-usb-u5
DST=/var/tmp/f8-pro-armbian/native-power-pm1
TOOL='/mnt/d/Netdisk/杂项/F8-PRO/archlinux/tools/f8_resource_image.py'
python3 - "$TOOL" <<'PY'
import sys, importlib.util
spec = importlib.util.spec_from_file_location('f8res', sys.argv[1])
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
old = open('/var/tmp/f8-pro-armbian/native-usb-u5/resource','rb').read()
newdtb = open('/var/tmp/f8-pro-armbian/native-power-pm1/fdt','rb').read()
# 确认新 dtb 无 cpufreq.off：
assert b'cpufreq.off' not in newdtb, 'new dtb still has cpufreq.off!'
out = m.replace_dtb(old, newdtb)
open('/var/tmp/f8-pro-armbian/native-power-pm1/resource','wb').write(out)
files = m.parse(out)
assert b'cpufreq.off' not in files['rk-kernel.dtb']
print('resource rebuilt:', len(out), 'bytes; dtb verified no cpufreq.off')
PY
# 重新打包 FIT（resource 变了）
cd "$DST"
mkimage -f boot.its boot.img
ls -la boot.img
sha256sum boot.img
echo BUILD_OK_V2
