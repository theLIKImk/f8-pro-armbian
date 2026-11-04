#!/bin/sh
# 触发后 rkcif 没有新日志 —— clr_unready_dev 只在 video_rkcif 模块参数上，
# 官方 Image 的 rkcif 没有以这个名字注册参数？但参数文件存在且写成功。
# 再看 pending 列表现在状态：
sudo -n cat /sys/kernel/debug/v4l2-async/pending_async_subdevices
echo MARKER_DONE
