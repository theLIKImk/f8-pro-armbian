# R3 真机结果：8 核、控制台与只读基础用户态通过

2026-10-29。用户报告 F: 日志盘，主助手确认卷标 F861R3，将 21 个文件保存到 local/hardware/armbian-6.1-r3-20261029-01/。test-result.json 保存哈希与结论。

## 已确认

- CPU1–7 都有 secondary processor 启动记录，SMP 日志共8核，CPUONLINE/CPUPOSS 均0-7。仍明确跳过 vendor cpufreq init；没有进行动态调频、压力或长期稳定性测试。
- UART2/ttyS2 注册并成为实际 console，earlycon正常交接，初始 console 打开失败的警告不再出现。没有外接UART收发测试。
- 原根分区完整PARTUUID核对后，/dev/mmcblk0p6 挂载为 ext4 ro,relatime,norecovery；识别 Arch Linux ARM，探测后正常卸载。没有重放日志、启动原systemd PID1/服务或改变原根分区身份。
- /usr/bin/true 退出0；systemd 262 --version 退出0，但仍报告 Failed to open /etc/systemd/user.conf: Function not implemented。该警告在此前旧内核记录中也存在，尚未定位；版本命令通过不等于PID1/服务兼容性通过。

采集快照到约启动后8.95秒，没有panic/Oops，USB日志导出正常。PARTS.TXT在eMMC枚举前已生成，故该单一文件没有MMC条目；后续dmesg和p6实际挂载提供了存储证据，不能把早期快照当作MMC消失。

## 下一步转向 Armbian 评估用户态

当前结果足以结束基础启动/CPU/原只读文件系统这一阶段。下一步使用已经构建的Trixie评估rootfs，不能因为原Arch版本命令的警告就认定目标Armbian会同样失败，也不能把原Arch基础程序通过当作Armbian已启动。

需要先恢复原BOOT并确认原SSH可用，之后将已校验的评估SquashFS放入原根分区的独立暂存目录，为RAM overlay/systemd试启动准备。这个准备步骤会新增镜像文件，不覆盖原系统；真正试启动时仍将原分区ro,noload挂载，写层在RAM。目标网络/SSH入口和日志通道还要明确，避免在没有可观测输出时直接启动完整桌面。

用户当前仍可能处于诊断版，尚无本次回退确认；日志已经全部保全，可立即只刷原BOOT恢复正常使用与充电。首测、R2、R3及原BOOT备份均保持原文件和哈希。
