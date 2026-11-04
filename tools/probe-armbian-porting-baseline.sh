#!/bin/sh
# Read-only; avoid network credentials and machine/SSH identities.
set -eu
printf 'KERNEL\n'
uname -r
printf 'I2C CLIENTS\n'
for d in /sys/bus/i2c/devices/*; do
    [ -f "$d/name" ] || continue
    case "$(cat "$d/name")" in
        *gsl*|*GSL*|*mpu*|*ak8963*|*cw2015*|*bq25890*|*es83*)
            printf '\n%s\n' "${d##*/}"
            cat "$d/name"
            readlink "$d/driver" || true
            readlink "$d/of_node" || true
            [ ! -f "$d/modalias" ] || cat "$d/modalias"
            ;;
    esac
done
printf '\nINPUT DEVICES\n'
cat /proc/bus/input/devices
printf '\nRELEVANT CONFIG\n'
zcat /proc/config.gz | sed -n '/CONFIG_TOUCHSCREEN_GSL/p;/CONFIG_GYROSCOPE_DEVICE/p;/CONFIG_GYRO_MPU6500/p;/CONFIG_MPU6500_ACC/p;/CONFIG_COMPASS_AK8963/p'
