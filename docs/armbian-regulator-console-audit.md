# R2 告警分类与 R3 控制台准备

2026-10-29，本轮只分析固定源码和已保存日志，没有平板访问或内核源码修改。

## regulator 的 device link 不是此处的供电失败

现场消息 `could not add device link regulator.N: -ENOENT` 对应固定 drivers/regulator/core.c 的 create_regulator：它已建立 regulator consumer 对象及内部链表，然后尝试 sysfs_create_link_nowarn，失败时用 rdev_dbg 输出，并明确标注 non-fatal，随后继续创建 debugfs/返回 consumer。这不是同名 device_link_add 的 PM 依赖链失败，也不能据该消息推断供电芯片 probe 失败。

R2 已有两颗 RK860 driver 链接、正常电压读回及 regulator_summary，支持它们实际绑定成功。ENOENT 所涉及的目标 kobject/创建时序没有逐步实测，故不宣称已经修复该 sysfs 链接；当前不为清除调试日志修改 regulator core，也不把它当作推进下一轮的阻塞条件。

## RGA 与初始 console

RGA 的全局 rga_init 在注册驱动后无条件调用 rga_iommu_bind；因此所有 DT 核心禁用也不会阻止聚合初始化报错。诊断没有 RGA 需求，该结果不证明硬件损坏，也无需为此重编内核。正式启用 RGA 时再检查它的完整 IOMMU/核心拓扑。

初始 console 警告来自 init/main.c 打开 /dev/console 失败。候选此前指定 ttyFIQ0，但并未实例化原厂 fiq-debugger 节点，只有 FIQ tty 驱动注册。R3 改为内建 8250 DW UART2：ttyS2，1500000n8，保留原厂 earlycon 地址 feb50000。

原厂 fiq-debugger 的 pinctrl 指向 uart2m0-xfer，即 GPIO0_B6/B5、function 10，与固定目标同名组一致；R2 pinmux 快照表明 pin13/14 未被占用。R3 显式覆盖默认 uart2m1 为 m0 并启用 UART2。Linux 控制台注册和硬件发送仍需 R3 检查；未连接 UART 时不能声称外部串口收发测试通过。

原始源码、SHA256 和片段保存在 analysis/armbian/regulator-console-audit/。
