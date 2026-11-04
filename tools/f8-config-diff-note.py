import re, subprocess

# C2 用的内核 Image 是 39471616 字节（10-29 构建，CONFIG_VIDEO_GC5035=m）。
# C3 新 Image 是 34300416 —— 小了 5.17MB。原因必查：
# 思路：用 dtc strings 对比两个 Image 的驱动字符串数量级差异；
# 或者更直接：查这次 make 改了哪些 CONFIG（olddefconfig 的副作用）。
# 我们没有旧 .config 备份，但 git 树里有 defconfig 源，且 evaluation-config.log
# 记录了上次构建配置。先看当前 .config 与 log 的差异痕迹。
print('检查 .config 中可疑的从 y 变 m / 被关闭的项 —— 与 evaluation-image.log 对照')
