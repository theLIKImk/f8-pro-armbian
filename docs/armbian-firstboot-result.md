# 首次 6.1 真机诊断结果

2026-10-29。用户刷入首测候选后报告日志盘出现；主助手确认 Windows F: 卷标 F861LOGS，将十个文件复制到 local/hardware/armbian-6.1-firstboot-20261029-01/，保存逐文件 SHA256 和 test-result.json。日志已保全，不需要继续停留在诊断系统。

## 通过的首测范围

- KERNEL.TXT 和 dmesg 确认 6.1.172-f8-pro-armbian-eval、AArch64，新诊断 DT 的 model/compatible 生效；3.160584 秒出现诊断 init 标记。
- eMMC 以 HS200/ADMA 枚举，mmcblk0 及 p1–p8 出现。只验证枚举，没有挂载原根分区或做存储写入测试。
- UDC 为 fc000000.usb；电脑实际识别只读 RAM FAT 日志盘，证明本次 USB2 设备模式及用户态导出链路可用。
- 新内核识别预期的四段内存；ramoops 成功注册。未测试 warm-reset 日志保持能力，也未区分 RAM banks 是静态快照保持还是 loader 重写所得。

这解决了本首测配置的新 FIT 接受、进入内核和运行 init 的问题。采集快照没有 panic/Oops；不代表长期稳定性、其他启动配置或完整安全启动策略已验证。

## 日志暴露的问题

1. I2C0 默认 i2c0m0 使用 GPIO0_B3/B4，与 SPI2 冲突，导致 CPU 大核 RK8602/3 所在总线未正常初始化。原厂实际使用 i2c0m2，即 GPIO0_D1/D2、function 3。草稿已改为 i2c0m2_xfer，新增原厂 pinctrl 选择及 pin/function 比对，最新 DT 320 项检查通过、无新增警告。原首测镜像未重建，修改尚未真机复测。
2. CPU4 的 regulator/OPP 初始化失败，cpufreq 延迟。RK860X 已内建，I2C0 冲突是首要待排除原因，但不能认为它必然是唯一原因。maxcpus=1 生效范围不扩大为 SMP/DVFS 验收；虽然传入 cpufreq.off=1，vendor OPP 探测仍实际发生，之前“关闭 cpufreq”的描述不能作为测量/电压路径完全禁用的保证。
3. display-subsystem 在 VOP 禁用时仍尝试探测并报 No available vop；RGA IOMMU 绑定失败，无声卡。首测没有启用这些功能，不能据此判定硬件损坏；后续诊断应明确关闭无关的父设备。
4. 零大小 logo/LUT 保留区警告、初始 console 无法打开，以及 regulator device-link/RK806 可选关机和睡眠状态缺失。后续在扩大到图形、休眠、充电和多核前处理，不把 USB 日志盘成功当成这些功能完成。

诊断日志在导出 USB 前封存，因此 dmesg 不含后续主机枚举过程；USB 成功由主机卷观测和用户反馈共同确认。STEPS.TXT 为空不代表失败，脚本前半段成功命令没有标准输出。

## 回退和下一步

用户已询问恢复原 BOOT 维持正常使用，已提供只写 boot 的 CURRENT-BOOT-ROLLBACK-64MiB.img 回退步骤；尚未收到回退完成确认。原备份 SHA256 为 7e51e71f7ec7439357e5ea2fbb97118715fe5fcf10401b638609df33567b1dd1。诊断版没有启用充电驱动，不用于长期运行或充电验收。

下一轮先验证 I2C0 mux 修正和核心供电，再逐项加入用户态、显示/GPU、触摸等。首测文件和回退文件保持原哈希，后续测试必须使用新版本文件名，避免覆盖本次证据。
