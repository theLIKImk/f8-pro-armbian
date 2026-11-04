import json

# C1 vs C2 差异回顾（依据 HANDOFF 与 camera-c2 文档）：
# C1: 两 sensor 的 pinctrl-0 都引用同一 MCLK pin（mipim1_camera1_clk），
#     GC5035 先 probe 占用 pin 成功；OV8858 后 probe 因 pin 冲突失败。
#     C1 运行时：22 个 video 节点存在（rkcif video 注册成功），media0/1 存在，
#     ISP 虚拟节点 initial probe 后 media2/3 出现。但 sensor subdev 依然没有
#     （C1 时也没有 gc5035 subdev —— 用户报"没有相机软件"，取帧未测）。
# C2: MCLK pinctrl 归 camera 电源 regulator 单一持有，sensor 节点删 pinctrl-0。
#     C2 运行时：双 sensor 都 probe 成功，但 rkcif video ENODEV（未注册）。
#
# C1 有 rkcif video、C2 没有 —— 这是重要差异！C2 的 pinctrl 改动可能影响了
# rkcif 的 notifier：rkcif probe 依赖 dphy→sensor 链完成才注册 video 节点？
# 不对：C1 时 sensor 也只成功了一颗……但至少 GC5035 的 subdev 应该在。
#
# 深层问题可能一直存在：官方 vendor gc5035 驱动 probe 成功但 subdev 不注册 ——
# 无论 C1 还是 C2。需要查 vendor 驱动源码确认注册路径。
print("需要 vendor gc5035 驱动源码分析。")
