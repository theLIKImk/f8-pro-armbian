sudo -n python3 -c "
import subprocess
# sensor remote=485 -> dphy1 ep1 phandle=485 匹配！DT 无问题。
# 那 sensor subdev 注册去哪了？看驱动源码里 detected 后的流程 —— 
# 官方 gc5035 驱动 (rockchip 版) detected 后要 power_on -> 初始化寄存器 -> 
# v4l2_i2c_subdev_init 在 probe 开头就调用 —— subdev 早就该有！
# 除非 probe 返回错误导致驱动 cleanup？但 i2c 设备 driver 还绑定着。
# 看 /sys/bus/i2c/devices/5-0037/driver 是否仍绑定 + driver version 打印时间:
print('checking i2c bind state via sysfs')
"
cat /sys/bus/i2c/devices/5-0037/uevent | grep DRIVER
echo M1
# 也许 subdev 注册成功但字符设备没创建？v4l2-subdev 的设备号：
ls -la /dev/v4l-subdev* | head -6
cat /sys/class/video4linux/v4l-subdev0/dev
echo M2
