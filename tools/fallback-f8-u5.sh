#!/bin/sh
# 不启动的现场取证。最可能原因（按概率）：
# 1. resource.img 重建导致 loader 读 cmdline/DTB 失败（project 已知用 f8_resource_image.py，
#    但 U5 镜像的 resource 可能不是 3 条目结构？—— 之前 parse assert count==3 通过了）
# 2. rockchip vendor cpufreq init 启用后因 DVFS/SCMI 依赖 panic
# 3. FDT 有既有问题
# 先回退：U5 镜像 SHA 已知。直接比对两者差异找死因需要串口日志，但用户没有串口。
# 安全路径：先给用户 U5 镜像回退，恢复在线，再用 UDISKS LOG 盘取证或只改一参数分步试。
echo "== U5 fallback image =="
ls -la /var/tmp/f8-pro-armbian/native-usb-u5/ 2>/dev/null
sha256sum /var/tmp/f8-pro-armbian/native-usb-u5/*.img 2>/dev/null || echo "boot.img 不在构建目录（只有组件）"
echo "== 检查 U5 最终镜像位置 =="
ls -la '/mnt/d/Netdisk/杂项/F8-PRO/archlinux/outputs/armbian/official-f8-native-usb-u5/'
echo DONE
