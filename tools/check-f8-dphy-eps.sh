#!/bin/sh
echo "== dphy1 ports 结构:"
sudo -n find /proc/device-tree/csi2-dphy1/ports -name 'endpoint' 2>/dev/null
echo "== dphy1 端点 remote/phandle:"
for ep in $(sudo -n find /proc/device-tree/csi2-dphy1/ports -name 'endpoint' 2>/dev/null); do
  echo "-- $ep"
  echo "   phandle: $(sudo -n fdtget /sys/firmware/fdt ${ep/\/proc\/device-tree/} linux,phandle 2>/dev/null)"
  echo "   remote:  $(sudo -n fdtget /sys/firmware/fdt ${ep/\/proc\/device-tree/} remote-endpoint 2>/dev/null)"
done
echo "== dphy2 端点:"
for ep in $(sudo -n find /proc/device-tree/csi2-dphy2/ports -name 'endpoint' 2>/dev/null); do
  echo "-- $ep"
  echo "   phandle: $(sudo -n fdtget /sys/firmware/fdt ${ep/\/proc\/device-tree/} linux,phandle 2>/dev/null)"
  echo "   remote:  $(sudo -n fdtget /sys/firmware/fdt ${ep/\/proc\/device-tree/} remote-endpoint 2>/dev/null)"
done
echo DONE
