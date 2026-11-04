#!/bin/sh
# 重载后 probe 成功但 subdev 数不变 —— sensor subdev 注册需要 dphy 的 notifier 端点。
# 检查 gc5035 probe 后是否调用了 v4l2_async_register_subdev（可能在等什么）：
echo "=== gc5035 dmesg after reload (full) ==="
sudo -n dmesg | grep gc5035 | tail -12
echo "=== i2c device state ==="
ls /sys/bus/i2c/devices/5-0037/
echo "=== 尝试 dphy 重 probe（禁令只禁 CIF unbind；dphy 未试过） ==="
# 先只读确认 dphy 当前绑定
readlink /sys/bus/platform/devices/csi2-dphy1/driver 2>/dev/null | xargs -r basename
echo MARKER_DONE
