#!/bin/sh
# remote-endpoint phandle 485/482 —— 查这些 phandle 属于哪些节点：
sudo -n python3 - <<'PY'
import subprocess
fdt = '/sys/firmware/fdt'
# 用 fdtgrep 不一定有；直接读 fdt 二进制找 phandle 引用节点
import re, struct
data = open('/sys/firmware/fdt','rb').read()
# 遍历找 linux,phandle == 485 / 482 的节点路径不易；改用 fdtget 列 dphy 节点端点：
# rockchip csi2-dphy0/1 在 /csi2-dphy0 (platform)。列出可能路径：
for p in ['/csi2-dphy0','/csi2-dphy1','/csi2-dphy2']:
    out = subprocess.run(['fdtget', fdt, p, 'compatible'], capture_output=True, text=True)
    print(p, '->', out.stdout.strip() or out.stderr.strip()[:60])
PY
echo "---cif mipi 节点:"
sudo -n find /proc/device-tree -maxdepth 1 -name '*lvds*' 2>/dev/null | head -5
sudo -n find /proc/device-tree -maxdepth 1 -name '*dphy*' 2>/dev/null | head -5
echo DONE
