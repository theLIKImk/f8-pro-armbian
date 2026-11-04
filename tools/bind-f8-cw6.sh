#!/bin/sh
sudo -n python3 -c "
for name in ['cw2015-battery', 'cw2015', 'cw2015_battery']:
    try:
        f = open('/sys/bus/i2c/devices/i2c-6/new_device', 'w')
        f.write(name + ' 6-0062')
        f.close()
        print(name, 'OK')
        break
    except Exception as e:
        print(name, 'FAIL', e)
"
sleep 2
ls /sys/bus/i2c/devices/ | grep 62 || echo no-device
dmesg | tail -3
echo DONE
