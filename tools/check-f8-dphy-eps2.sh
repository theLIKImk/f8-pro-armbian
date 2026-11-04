#!/bin/sh
for ep in /csi2-dphy1/ports/port@0/endpoint@1 /csi2-dphy1/ports/port@1/endpoint@0 /csi2-dphy2/ports/port@0/endpoint@1 /csi2-dphy2/ports/port@1/endpoint@0; do
  echo "== $ep"
  echo "   phandle: $(sudo -n fdtget /sys/firmware/fdt $ep linux,phandle 2>/dev/null)"
  echo "   remote:  $(sudo -n fdtget /sys/firmware/fdt $ep remote-endpoint 2>/dev/null)"
  echo "   data-lanes: $(sudo -n fdtget /sys/firmware/fdt $ep data-lanes 2>/dev/null)"
done
echo DONE
