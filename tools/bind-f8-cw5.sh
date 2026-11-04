#!/bin/sh
# 之前两次 "Extra parameters" 是因为 tee 命令行格式问题？不——Extra parameters
# 表示给了多余 token。可能 shell 展开问题。用 python 单行写，逐次尝试三种名字：
sudo -n python3 - <<'PY'
for name in ['cw2015-battery', 'cw2015', 'cw2015_battery']:
    try:
        with open('/sys/bus/i2c/devices/i2c-6/new_device', 'w') as f:
            f.write(f'{name} 6-0062')
        print(name, 'OK')
        break
    except Exception as e:
        print(name, 'FAIL', e)
PY
sleep 2
ls /sys/bus/i2c/devices/ | grep 62 || echo no-device
dmesg | tail -3
echo DONE
