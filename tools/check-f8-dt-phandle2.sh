sudo -n fdtget /sys/firmware/fdt /csi2-dphy1/ports/port@0/endpoint@1 phandle
echo M1
sudo -n fdtget /sys/firmware/fdt /i2c@fead0000/gc5035@37/port/endpoint remote-endpoint
echo M2
