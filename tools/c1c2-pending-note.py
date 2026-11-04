import json

# 决定性证据解读（C1 front-reprobe01.json 的 pending_before）：
# pending 列表里已经存在 m01_f_gc5035 5-0037（sensor subdev 已注册但 pending！）
# 且 rkcif-mipi-lvds2、rkcif-mipi-lvds3、dphy1/2、mipi-csi2×2 全部在 pending 列表 ——
# 说明 C1 时整条链的 notifier 都在等待，从未 complete！
# rkcif video 节点（22个）在 C1 存在 —— video 注册不依赖 notifier complete。
# rkisp 虚拟设备 probe 失败（failed attach isp hw）是因为 rkisp_hw 也 pending。
#
# C2 情况：rkcif-mipi-lvds2/3 "Async subdev notifier completed" —— 什么变了？
# C2 改动把 MCLK pinctrl 从 sensor 移到电源 regulator。这不该影响 async。
# 但 C2 让 OV8858 也 probe 成功了。C1 只有一个 sensor 成功 —— pending 列表里
# 两个 csi2 都在等。complete 需要"所有匹配项都到齐"——rkcif 的 notifier 匹配表
# 只含 sditf fwnode，sditf 出现即 complete？但 C1 时 sditf 也注册了（pending
# 显示 rkisp 在等 sditf，sditf 自己 pending 等 cif）……
# v4l2-async 的等待链：rkisp 等 sditf，sditf 等 cif，cif 等 mipi-csi2，
# mipi-csi2 等 dphy，dphy 等 sensor。C1 时全部 pending —— 链没 complete。
# C2 时 rkcif "completed" 了 —— 说明 C2 的 rkcif notifier 匹配完成 ——
# 这反而说明 C2 的链比 C1 更完整！但 C2 的 rkcif video 却 ENODEV……
# 重新看 C2 dmesg："clear unready subdev num: 1" + "Async subdev notifier completed"
# clear unready=1 表示还剩1个未就绪 subdev 被强制放弃。
# C2 的 rkcif 在等谁？mipi-csi2 port0 的 sensor fwnode —— sensor probe 在 7.2s，
# rkcif probe 在 2.6s 只等到 mipi-csi2（2.4s probe），等到1个未就绪就……
# "clear unready subdev num: 1" 是 rkcif 放弃等待 sensor 的标志！
# C1 里 pending 全链挂着不 complete（永远等）；C2 里 rkcif 主动放弃等待。
# 差异可能在于 C2 的 rkcif probe 时机/顺序变化。
print("C1: 全链 pending 挂起（video 节点存在）；C2: rkcif 主动放弃等待 sensor")
print("下一步：读取 C2 的 pending_async_subdevices 现状，确认当前哪些在 pending")
