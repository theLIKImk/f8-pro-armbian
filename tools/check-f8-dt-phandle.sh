#!/bin/sh
# "detected gc5035 sensor" 之后 sensor 驱动就沉默了 —— subdev 注册悄悄失败或没走到。
# 看 probe 里 detected 之后代码做什么：注册 media pad、v4l2_async_register_subdev。
# 如果 fwnode graph 解析失败（sensor endpoint 的 remote 指向 dphy 端点——
# 需确认 dphy 端点 phandle 在 DTB 里有 phandle 属性！）
# 之前 C2 fdt 解析：dphy1 port@0/endpoint@1 有 phandle=0x1de 吗？
# 运行DT检查 sensor endpoint remote 指向的目标端点有没有 phandle：
sudo -n fdtget /sys/firmware/fdt /csi2-dphy1/ports/port@0/endpoint@1 phandle 2>/dev/null || echo NO_PHANDLE
sudo -n fdtget /sys/firmware/fdt /csi2-dphy1/ports/port@0 2>/dev/null
echo M1
# 对照 gc5035 endpoint：
sudo -n fdtget /sys/firmware/fdt /i2c@fead0000/gc5035@37/port/endpoint phandle remote-endpoint 2>/dev/null
echo MARKER_DONE
