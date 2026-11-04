# F8-PRO 电源三档模式：当前受挫与下一步（2026-11-01）

> 接续复核：下文“vendor 初始化即崩”是基于启动现象的推测，缺少内核日志，不能当作已定位结论。“失败无副作用”“零内核风险”也未经验证。运行时 probe、模块加载、SCMI 调频均先暂缓，优先查匹配内核源码及建立启动取证路径。最新实机与配置见 [接续核对](armbian-handoff-reconciliation-20261101.md)。

## 目标

为 KDE 提供 省电/平衡/性能 三档电源模式（powerdevil/powerprofilesctl 路径）。

## 发现的现状

- 当前 BOOT 的 cmdline 含两个保守参数（早期 I2C 供电冲突调试时代遗留）：
  - `cpufreq.off=1`
  - `initcall_blacklist=rockchip_cpufreq_driver_init`
- 后果：CPU 全部锁定 816MHz（SCMI clk_summary 确认三个集群均 816MHz），无 governor，三档无从谈起。
- DT 完备：`cluster0/1/2-opp-table`、`dmc/gpu/npu-opp-table` 都在；cpu-supply（RK8602/3）自 R2 轮起已验证。

## 失败实验记录（用户已两次手动回退恢复）

| 版本 | 改动 | resource.img | 结果 |
| --- | --- | --- | --- |
| PM1 | 去掉两参数 | 用 f8_resource_image.py 重建 | 不启动 |
| PM1-A | 只去 initcall_blacklist（保留 cpufreq.off=1） | 原封不动（U5 原件） | 不启动，背光不亮 |

产物（留档勿刷）：
- `outputs/armbian/official-f8-power-pm1/BOOT_ONLY_ARMBIAN_POWER_PM1.img`（SHA 7f065a39…）
- `outputs/armbian/official-f8-power-pm1a/BOOT_ONLY_ARMBIAN_POWER_PM1A.img`（SHA b873802b…）

回退文件（已验证可启动）：
- `outputs/armbian/official-f8-native-usb-u5/BOOT_ONLY_ARMBIAN_NATIVE_USB_U5.img`（SHA 9044ece3…8c5e237）

## 结论

**vendor `rockchip_cpufreq_driver_init` 一初始化即崩**——PM1-A 中 cpufreq 依然被 off（无行为变化可能），唯一变量是解除黑名单，结果整机早期崩溃。与 resource.img 重建无关（PM1-A 用原件仍死）。这也是它当初被拉进黑名单的原因。

取证受限：pstore/ramoops 只有 5.10.160 原厂内核一次日志，vendor 6.1 内核未启用 ramoops，两次失败均无内核日志。

## 下一步候选（风险从低到高）

1. **运行时加载 cpufreq-dt 通用驱动**（推荐首选）：
   - 不改 cmdline，设备上 insmod 测试，失败无副作用
   - DT OPP 表齐全；内核已内建 `cpufreq-dt` platform driver（sysfs 确认）
   - 需实测：`cpufreq.off=1` 对运行时模块加载的拦截语义（它可能只挡 boot 时注册）
2. userspace 直调 SCMI clk 限频（无 governor，功能弱但零内核风险）
3. 修 vendor 驱动崩溃依赖：需要串口日志定位 panic 位置，当前无串口

## 教训

- BOOT-only 改动也要逐步二分：PM1 同步改了 cmdline+resource 两个变量，第一次失败后无法归因；PM1-A 单变量才锁定元凶。
- 本项目的 BOOT 构建链（f8_resource_image.py 严格校验重建）本身可信，非死因。
