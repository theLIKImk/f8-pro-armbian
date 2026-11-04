# 6.1 首次硬件测试

2026-10-29 更新：本次已由用户刷入并出现 F861LOGS；新内核/init、eMMC 枚举和 USB 日志盘达到首测目标。日志已复制保存，结果见 docs/armbian-firstboot-result.md。用户可以按回退步骤恢复原 BOOT；以下“尚未写入”是制包时的历史状态。

这是最小启动诊断，不等待桌面或全部外设完成。候选与当前 boot 回退备份已经生成；离线准备就绪不代表硬件启动成功。尚未写入平板或取得本次部署确认。

## 测什么

启动 6.1.172-f8-pro-armbian-eval，进入专用 init，枚举 eMMC，向电脑导出只读 RAM 日志盘。不挂载任何物理分区，不启动 Arch/Armbian systemd、桌面或 SSH。首测期间屏幕可能保持原 Logo 或没有图像，SSH 也不会上线，均不能单独作为失败判断。

候选只启用 USB0 的 USB2 fixed-peripheral 路径，去掉 USB3 PHY、role-switch 和跳过 PHY init 的旧 quirk；目标 PHY 源码确实从控制器读取 dr_mode，并防止固定 peripheral 被 ID 中断切换到 host。没有启用 TCPC/PD、充电策略、触摸、GPU 或面板。USB 电气行为仍需这次硬件试验确认。

DT 使用原板 compatible，RAM banks 和 vendor-storage 预留来自本设备旧启动观测，作为首测快照；loader 仍可能修补这些内容。CPU 限制单核，关闭 cpufreq。earlycon 地址沿用原厂参数，但没有外接 UART 时不能依赖串口观测。

## 文件与校验

目录：outputs/armbian/firstboot-diagnostic/。

- 首测：BOOT_ONLY_6.1_FIRSTBOOT_CANDIDATE.img，40889988 字节，SHA256 98037112b015172461c9eb776aba6b85acee8aa080ec74a08c8aba90dc49b496。
- 回退：CURRENT-BOOT-ROLLBACK-64MiB.img，67108864 字节，SHA256 7e51e71f7ec7439357e5ea2fbb97118715fe5fcf10401b638609df33567b1dd1。

回退文件是从当前 /dev/mmcblk0p3 完整只读回读，核验 PARTUUID、起始 LBA 0x8000、大小 0x20000 扇区；本地与设备端 SHA256 一致，FIT 四个 payload 的内部哈希全部通过。其 ramdisk 大小还与当前运行 DT 的 initrd 地址跨度一致。文件是 boot 分区原始备份，不是完整系统备份。

候选已通过 DT 编译/无新增警告、必要 USB/FAT/pstore 内建配置、ARM64 静态 BusyBox/所需 applet、init shell 语法、RAM FAT fsck、新 cpio 回读及 FIT 四 payload 哈希检查。使用旧观测 kernel/initrd 起点与默认 DT 地址进行几何检查，已包含 DT 12KiB 扩容，没有重叠；不是新内核真实交接地址证明。详见 preflight.json。

## 实际测试步骤（用户协调后执行）

1. 保存当前工作，确认电脑能通过此前使用的 RK 工具识别平板 Loader，并保留上面的回退文件。
2. 进入 Loader，使用“下载镜像”，读取实际分区表。仅勾选 boot，确认起点 0x00008000、分区大小 0x00020000 扇区，选择首测候选文件。不要使用“升级固件”、擦除或勾选其他分区。
3. 写入 boot 后启动，USB 保持连接电脑。等待约 60 秒，查看是否出现名为 F861LOGS 的日志盘；USB0 控制器未枚举时可能不出现，需记录电脑检测到的 USB 设备及现象。
4. 若日志盘出现，复制全部文件到独立的新测试目录。KERNEL.TXT 应显示 6.1.172-f8-pro-armbian-eval；DMESG.TXT、PARTS.TXT、DEVICES.TXT、IOMEM.TXT 用于判断内核、eMMC、PHY/UDC 等状态。日志是暴露 USB 前封存的快照，不会持续刷新。
5. 采集后恢复原系统：重新进入 Loader，仅选择 boot，写回 CURRENT-BOOT-ROLLBACK-64MiB.img，再启动并确认原 Arch SSH 恢复。如果首测没有 USB 日志盘，仍按同一步骤回退；若无法重新进入 Loader，先停止，不尝试擦除其他分区。

本次写 boot 和重启会暂时中断原系统。首测通过后，再逐步测试内屏/GPU、触摸、网络、音频与 Wayland；不把日志盘出现当成桌面或全部硬件完成。
