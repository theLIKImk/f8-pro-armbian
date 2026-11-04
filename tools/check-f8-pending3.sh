#!/bin/sh
# pending 列表里所有组件都在等待 —— 整条链 pending，没人 complete。
# 但 2.6s 时 rkcif 打了 "Async subdev notifier completed"！矛盾？
# 再读一遍 pending 语义：pending_async_subdevices 显示的是"还在等的 notifier"
# —— rkcif 已 complete 所以不在列表；列表里是 sensor/rkisp/dphy/mipi-csi2
# 这些"等待别人"的。rkisp 等 sditf，sditf 等 cif（已complete→不会回来匹配）。
# dphy 等 sensor，sensor 等 dphy —— 互等死锁！
# sensor 的 v4l2_async_register_subdev_sensor 注册后应匹配 dphy 的 asd ——
# 都在 pending 列表却互不匹配，说明 v4l2-async 的 fwnode 匹配失败。
# sensor endpoint remote=dphy ep1(485)，dphy ep1 remote=sensor ep。
# v4l2 匹配用 fwnode：sensor 的 endpoint fwnode vs dphy asd 的 fwnode。
# 关键：dphy notifier 的 asd 是用什么 fwnode 注册的？dphy 驱动遍历自己的
# port@0/endpoint@1 的 remote —— 指向 sensor endpoint node。
# sensor 注册 subdev_sensor 时用 endpoint 的 fwnode —— 应该匹配！
# 除非：C2 删了 sensor 的 port/endpoint 节点？—— 不，前面 fdtget 确认存在。
# 再细看 pending 输出：m01_f_gc5035 5-0037: 后面没有 [fwnode] 行 ——
# 它是 subdev 的 pending；dphy 也是。两个互相等。v4l2_async 应该在注册时
# 立即互相匹配。不匹配的原因：dphy 的 asd fwnode 与 sensor 的 subdev fwnode
# 不同级 —— dphy asd 指向 sensor 的 **endpoint** node，而 sensor subdev
# 注册时用 dev fwnode（i2c 节点）而非 endpoint node！
# v4l2_async_register_subdev_sensor 会额外注册 endpoint-async？
# 6.1 内核 v4l2_async_register_subdev_sensor(sd) 内部会为每个 port/endpoint
# 注册 ancillary —— 应该能匹配。
# 现在做个直接实验：手动看 dphy notifier 的 asd fwnode 是什么。
sudo -n cat /sys/kernel/debug/v4l2-async/pending_async_subdevices | head -3
echo M1
# 对照 C1 证据里的 pending_before —— C1 时 sensor 也在 pending，跟现在一样。
# C1 时 rkcif video 是注册成功的！说明 pending 状态不影响 video 注册。
# C2 的 video ENODEV 一定另有原因。查 C2 rkcif probe 是否注册 video 失败：
sudo -n dmesg | grep -E 'rkcif rkcif-mipi-lvds2' | grep -viE 'sensor info|update' | head -8
echo MARKER_DONE
