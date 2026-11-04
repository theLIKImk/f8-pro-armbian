# R4 真机结果（2026-10-29）

F: 卷标 F861R4 已确认，18份原始日志保存到 local/hardware/armbian-6.1-r4-20261029-01/，summarize-f8-fourthboot.py 校验并生成含逐文件 SHA256 的 test-result.json。原 R4 与回退镜像未改。

评估用户态首次真正运行：Debian 13 Trixie 的 systemd 257.13-1~deb13u1 为 PID1，f8-evaluation.target active，CPU0–7在线，ttyS2 console 保留。journal 报告启动完成约21.674秒（其计时口径）；导出快照不是长期稳定性测试。

原 /dev/mmcblk0p6 挂载为 ext4 ro,norecovery；暂存 SquashFS 完整 SHA 校验成功，lower 只读，根目录为 overlay，upper/work 在 /run tmpfs。目标写入留在RAM。systemd-pstore 将上一轮 ramoops 搬到 RAM overlay 中的 /var/lib/systemd/pstore；本次未导出该文件内容。设备时间回退到 systemd 内置 epoch，journal 日期不是实际测试日期。

存在一项失败：systemd-resolved.service 多次以 200/CHDIR 退出，并报连接 journal socket Permission denied，整体为 degraded。专用 target 仍然 active，不能记录为全部服务正常。init 的 umask 077 使新建 overlay upper 默认为0700，这是非root服务无法遍历根目录的高概率原因；本次没有 stat 根目录权限证据，下一候选需明确设置 upper/root 0755 并增加权限与服务身份日志，不能仅 mask DNS 来掩盖问题。

新注入单元因 cp 受 umask 影响出现 world-inaccessible 告警；旧 SSH hostkey 单元仍有 executable/world-writable 告警。下一版本在 RAM overlay 中明确设置单元0644、必要公共目录0755；冻结 SquashFS 和共享 hardlink 验证树不要原地修改。构建主机 hostname 仍留在评估镜像，应在后续RAM配置中替换。

快照无 Kernel panic/Oops。udevd/journald/basic target 启动，vendor cpufreq 仍被黑名单跳过；RGA聚合绑定/早期 regulatory.db 缺失等告警仍在。basic target 还自动拉起常规 timers 和本地 AF_UNIX SSH socket，不等于 TCP SSH 或联网成功。后续评估需收敛无关 timers，并补充模块、固件和权限检查。

Wayland/SDDM、显示/GPU、触摸、充电、网络、DVFS和负载仍未验收。日志已保全，可立即只刷原 BOOT 回退使用/充电；截至记录尚未确认本次回退。下一步先修复 RAM overlay 权限，再推进图形与触摸候选。
