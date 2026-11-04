sudo -n python3 -c "
import os
# video0 dev=81:0 存在于 sysfs 与 /dev（81:0）。open ENODEV 说明 cdev 没注册。
# v4l2: video_register_device 成功才有 cdev。sysfs 有 = 注册成功过。
# 但 open ENODEV = video_device 的 vfl_devnode 检查失败？
# 实际上 ENODEV 在 open 时意味着 video_device 被注销了（video_unregister_device）。
# 谁注销 rkcif video？notifier complete 前后？C2 时序：
#   2.4s rkcif probe + 注册 video 节点
#   2.6s notifier complete
#   7.2s sensor probe
# 之后谁 unbind？可能 rkcif 在 'There is not terminal subdev' 后自己注销 video！
# 查 dev.c 里 unregister 调用与 'terminal subdev' 关联：
print('need dmesg around video unregister')
"
sudo -n dmesg | grep -iE 'unregister|rkcif-mipi-lvds2: ' | grep -vE 'apparmor|audit|sensor info' | tail -12
echo MARKER_DONE
