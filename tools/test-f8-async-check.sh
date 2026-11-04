#!/bin/sh
# 有个重大发现机会：sensor probe 成功但 subdev 没注册 —— 官方 gc5035 驱动里
# v4l2_async_register_subdev 会被调用。它注册到 v4l2 的 async 子系统，
# 然后尝试匹配 pending notifier。dphy 的 notifier 可能还在等待（因为 dphy
# probe 时 sensor 还没好）—— 但 media0 显示 dphy 已 linked……
# 实测验证 v4l2-async 行为：重载 sensor 后 dmesg 会出现 "Async registered subdev"？
# 刚才 tail 没看到。用明确 grep：
sudo -n dmesg | grep -iE 'async' | tail -8
echo "=== sensor subdev 到底注册没有？检查 /dev/v4l-subdev* 的 name ==="
for s in /sys/class/video4linux/v4l-subdev*; do
  echo "$(basename $s): $(cat $s/name)"
done
echo MARKER_DONE
