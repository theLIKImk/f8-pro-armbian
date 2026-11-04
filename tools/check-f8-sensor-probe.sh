#!/bin/sh
# 诊断结论已明确：
# - 只有 rkisp (video22-39) 可开；所有 rkcif video 节点 ENODEV —— CIF 的 video 设备
#   没有注册到 V4L2 core（video_register_device 未跑或失败），但 sysfs 名字残留。
# - 内核日志 rkcif_update_sensor_info "get remote terminal sensor failed -19" ——
#   CIF 在 streamon 时找不到 sensor 端点。
# 根因方向：CIF async notifier 等待 sensor subdev，但 sensor 的 v4l2 subdev
# 从未注册（44 个节点无 gc5035/ov8858 subdev）。C2 启动服务只做了
# "drivers_probe initial probe"（ISP 虚拟设备），没让 sensor 注册 subdev？
# 但 dmesg 显示 sensor probe 成功（driver version/detected）。
# 关键：rkisp "Async subdev notifier completed" 在 2.68s —— CIF 完成时 sensor
# 还没 probe（7.2s）。SDITF 链需要 sensor。
# sensor subdev 没进 media 图的可能原因：gc5035/ov8858 驱动的 subdev 注册成功
# 但 async 匹配失败（endpoint 数量不匹配）→ sensor subdev 挂在 v4l2 但 media
# 图不显示。检查 /dev/v4l-subdev* 只有4个 —— sensor subdev 根本没注册成字符设备。
# 驱动 probe 返回 0 了吗？
sudo -n dmesg | grep -E 'gc5035 5-0037|ov8858 5-0036' | tail -12
echo DONE
