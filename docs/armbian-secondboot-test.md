# R2：I2C0 与大核供电芯片诊断

2026-10-29 更新：用户已完成 R2 启动，F861R2 日志已保存。I2C0 m2、RK8602/3 绑定和 initcall 黑名单达到本轮目标；结果见 docs/armbian-secondboot-result.md。下文“尚未刷入”是制包时状态。

首测已经证明新内核、eMMC 枚举和 USB 日志盘可以工作。R2 只处理其日志暴露的核心供电总线问题，不启动桌面、不挂载物理根分区、不测试充电或多核调频。

## 改动与验证

- I2C0 改为原厂 i2c0m2_xfer（GPIO0_D1/D2、function 3），消除与 SPI2 默认 pinmux 的冲突。DT 原厂比对 320 项通过。
- 保留 maxcpus=1/cpufreq.off=1，并增加 initcall_blacklist=rockchip_cpufreq_driver_init。固定源码和现有 vmlinux 确认该初始化符号；实际黑名单生效情况需要本次日志确认。这样先验证 RK8602/3 绑定，不把 vendor OPP 校准混进同一轮。
- 关闭未测试的 display-subsystem、三个 RGA 核心，删除无显示时的零大小 logo/LUT 占位。console/regulator device-link 等其他问题尚未宣称修复。
- 在 RAM 日志快照前多等 5 秒，额外保存 CPURAILS.TXT、REGULATR.TXT、PINMUX.TXT、CPUONLINE.TXT、CPUFREQ.TXT，均为只读查询，没有原始 I2C 写入或电压设置。

候选文件：outputs/armbian/firstboot-diagnostic-r2/BOOT_ONLY_6.1_DIAGNOSTIC_R2_CANDIDATE.img。

大小 40890232 字节，SHA256 17762adae7a830ffd72be3dd2842d5a6b124c24d1ad30738c06141616586d3a3。DT 无新增警告，cpio/ARM64 shell/FAT/FIT payload 和含 12KiB 的布局检查通过。Image 与首测完全相同，不是新编译内核；变化是 DT 和诊断 initramfs。新 USB 序列号与卷标避免和首测日志混淆。

## 测试方法

1. 进入之前已成功使用的 Loader，在 RKDevTool“下载镜像”中只选 boot（起点 0x00008000，大小 0x00020000 扇区）。选择 R2 候选，不擦除、不勾选其他分区。
2. 启动后 USB 连电脑，等待约 60 秒，应出现 F861R2 日志盘。复制全部文件；日志封存后不持续刷新。没有桌面或 SSH。
3. 重点看 DMESG.TXT 是否仍有 I2C0/SPI2 冲突、是否确认黑名单跳过 vendor cpufreq init；CPURAILS.TXT 应出现 0-0042 和 0-0043 的 driver 链接，PINMUX/REGULATR 用于核对实际管脚和供电读数。供电芯片绑定通过也不等于 DVFS/SMP 通过。
4. 采集后按首测相同步骤，只写 boot 恢复原系统，使用 outputs/armbian/firstboot-diagnostic/CURRENT-BOOT-ROLLBACK-64MiB.img；该备份与首测包哈希已复核未变。若不出现日志盘，同样回退后报告现象。

R2 尚未刷入或硬件验证。用户可以保持原 BOOT 正常使用，方便时再做这次短测；不要依靠诊断版验收充电。后续包不得覆盖首测或 R2 文件。
