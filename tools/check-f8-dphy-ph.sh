#!/bin/sh
# sensor endpoint remote 485/482 —— 查 csi2-dphy1/dphy2 的 port endpoint phandle：
echo "== csi2-dphy1 ports:"
sudo -n fdtget /sys/firmware/fdt /csi2-dphy1 ports 2>/dev/null
sudo -n fdtget /sys/firmware/fdt /csi2-dphy1/status 2>/dev/null
sudo -n ls /proc/device-tree/csi2-dphy1/ 2>/dev/null | head
echo "== dphy1 端点 phandle:"
sudo -n fdtget /sys/firmware/fdt /csi2-dphy1/port@0/endpoint linux,phandle 2>/dev/null
sudo -n fdtget /sys/firmware/fdt /csi2-dphy1/ports/port@0/endpoint linux,phandle 2>/dev/null
echo "== csi2-dphy2 status 与端点:"
sudo -n fdtget /sys/firmware/fdt /csi2-dphy2/status 2>/dev/null
sudo -n fdtget /sys/firmware/fdt /csi2-dphy2/ports/port@0/endpoint linux,phandle 2>/dev/null
sudo -n fdtget /sys/firmware/fdt /csi2-dphy2/port@0/endpoint linux,phandle 2>/dev/null
echo DONE
