import json

# 重大修正！官方 vendor Image 里 rkcif/rkisp/dphy 全部是**模块**（modules.builtin 里
# 有它们但列表显示的是 .ko 文件 —— modules.builtin 列出的是内建文件路径？
# 不对：modules.builtin 列出的就是内建模块的路径（编译为 =y 时也会有条目，
# 但内核实际没有 .ko）。而 modules.order 列出 sensor .ko 说明 sensor 是模块。
# 关键混淆点：modules.builtin 里的条目对应 =y 编译的驱动（无 .ko 文件）。
# 但路径带 .ko 只是命名惯例。所以 rkcif/rkisp/dphy-hw 是内建（=y），sensor 是模块（=m）。
#
# 等一下 —— 设备 lsmod 只显示 gc5035/ov8858 两个视频模块，rkcif/rkisp/dphy 不在
# lsmod → 它们是内建。确认。
#
# 那么时序问题确认。但原厂 5.10 也是同样的内建 rkcif + 模块 sensor？
# 原厂 5.10 rootfs 是 Android 式启动，sensor 模块通过 vendor init.rc 很早 insmod？
# 不对 —— 原厂 5.10 的 rkcif 也内建，sensor 模块后加载，原厂也能出图！
# 说明 **rkcif 的 notifier complete 后，迟到的 sensor subdev 是能挂上的** ——
# 通过 rkcif 的 bridge/sditf 机制在 streamon 时 walk graph。
# 而 6.1.115 vendor 内核在 C1 上 22 个 video 节点都注册了（说明 notifier 机制 OK），
# sensor subdev 没 devnode 也正常（未 host 认领）。
# 那为什么 C2 的 rkcif video 反而 ENODEV？！C1→C2 只改了 MCLK pinctrl 归属！
# 重大嫌疑：C2 让 GC5035/OV8858 都 probe 成功 → 两个 sensor 都调
# v4l2_async_register_subdev_sensor → 它会注册 sensor 的 fwnode endpoint 到
# async 系统。而 rkcif notifier complete 需要等所有 remote endpoint……
# C1：只有 GC5035 probe 成功（OV 失败）→ notifier 逻辑？
# 但 C1 22 节点注册了 —— C2 双 sensor 都成功反而让 rkcif 不注册？
# 反直觉。真正需要的是 C1 与 C2 的 media 图对比。
print("需要 C1 运行时 media 图证据对比")
