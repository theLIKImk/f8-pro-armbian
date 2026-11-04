# Inserted before the R2 log snapshot is closed. Read-only metadata queries.
sleep 5
echo 'I2C0 regulator drivers, no raw I2C access' >/run/logdisk/CPURAILS.TXT
for client in /sys/bus/i2c/devices/0-0042 /sys/bus/i2c/devices/0-0043; do
    echo "$client" >>/run/logdisk/CPURAILS.TXT
    ls -ld "$client" "$client/driver" >>/run/logdisk/CPURAILS.TXT 2>&1
    for field in name modalias; do
        [ ! -f "$client/$field" ] || cat "$client/$field" >>/run/logdisk/CPURAILS.TXT
    done
done
cat /sys/devices/system/cpu/online >/run/logdisk/CPUONLINE.TXT
ls -l /sys/devices/system/cpu/cpufreq >/run/logdisk/CPUFREQ.TXT 2>&1
mkdir -p /sys/kernel/debug
if mount -t debugfs debugfs /sys/kernel/debug; then
    cat /sys/kernel/debug/regulator/regulator_summary >/run/logdisk/REGULATR.TXT 2>&1
    for pins in /sys/kernel/debug/pinctrl/*/pinmux-pins; do
        [ ! -f "$pins" ] || cat "$pins" >>/run/logdisk/PINMUX.TXT
    done
fi
echo 'F8 R2 REGULATOR SNAPSHOT COMPLETE' >/dev/kmsg
