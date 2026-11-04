#!/bin/sh
sudo -n python3 -c "
f = open('/sys/bus/i2c/devices/i2c-6/new_device', 'w')
f.write('cw2015 0x62')
f.close()
print('written')
"
ls /sys/bus/i2c/devices/ | grep 62
dmesg | tail -2
echo DONE
