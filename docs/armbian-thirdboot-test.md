# R3：8 核启动与只读用户态测试

2026-10-29 更新：R3已由用户完成并保存F861R3日志。8核、ttyS2及ro,norecovery挂载/卸载达到目标，true/systemd --version均退出0；systemd仍有Function not implemented警告，PID1未测。结果见docs/armbian-thirdboot-result.md。以下未部署状态为制包时历史。

本轮合并验证 SMP、控制台和只读文件系统/用户态，继续使用已通过首测的 6.1.172 Image，不启动桌面，不进行压力、动态调频、充电或休眠测试。

## 本轮范围

- 去掉 maxcpus=1，让固件/PSCI 唤醒 8 个 CPU；保留 cpufreq.off=1 和已在 R2 证实生效的 vendor initcall 黑名单，不主动设置频率或电压。是否全部上线、是否稳定到采集阶段由本轮确认。
- UART2 使用原厂 m0 管脚，console 改为 ttyS2。检查 CONSOLE.TXT 和 dmesg 的控制台注册，不要求用户外接 UART。
- 核对原根分区完整 PARTUUID，仅以 ext4 ro,noload 挂载，不重放日志；确认 Arch 标记后限时执行 /usr/bin/true 与 systemd --version。不是运行 PID1、服务、SSH、用户初始化或完整 Armbian 用户态。
- 读取完成后卸载原根分区，再封存并导出只读 RAM 日志盘。原数据/身份/密钥不修改，日志只复制 os-release、mount 元数据及版本/退出码。

## 文件

首测候选：outputs/armbian/firstboot-diagnostic-r3/BOOT_ONLY_6.1_DIAGNOSTIC_R3_CANDIDATE.img。

42118860 字节，SHA256 16c32f21ab9deba9550b04a8933bbe22a4ffb2d61f2c196bce4dfa924c852000。DT 编译无新增警告，实际打包的 blkid/libblkid 运行依赖通过 ARM64 QEMU --version 检查；shell、cpio/FAT/FIT 和含 DT 扩容的布局检查通过。离线检查不等于新测试已经通过。

## 操作与判定

1. 使用已成功的 Loader/RKDevTool“下载镜像”，只勾 boot（起点 0x00008000，大小 0x00020000 扇区），选择 R3，不擦除、不写其他分区。
2. 启动保持 USB 连接，等待约 60 秒，检查 **F861R3** 日志盘并复制全部文件。
3. CPUONLINE.TXT 预期 0-7，dmesg 预期 8 processors activated；CONSOLE.TXT 应含 ttyS2。MOUNTS.TXT 核对原根分区为只读、noload/norecovery；RUNTRUE.TXT、RUNSYS.TXT 记录退出码，ROOTPROBE.TXT 记录身份/失败原因。systemd --version 成功不等于 systemd PID1 成功。
4. 完成或未见日志盘，都按已有方法只写 boot 恢复原备份 CURRENT-BOOT-ROLLBACK-64MiB.img（位于 firstboot-diagnostic 目录），确认原系统与充电/SSH。不要把诊断版作为日常系统。

R3 尚未部署。恢复原系统后仍可继续本地适配，不需要保持诊断在线。
