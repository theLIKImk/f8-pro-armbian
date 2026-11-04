# F8-PRO CPU供电、内存与监测配置

## 2026-10-29 CPU OPP 静态补充

tools/audit-f8-cpu-opp.py 已逐项读取原厂与候选 DTB。候选三组 OPP 数量为 24/32/32，原厂为 17/23/23；新增内容包含不同芯片分档，不能理解为同一芯片全部可选的频率。所有候选 opp-microvolt 及其 L/B 变体的目标电压均在原板稳压器范围内，三组越界数均为 0；这不代表运行时分档选择或 DVFS 稳定性已验证。

原厂共有的 leakage、opp-info、specification_serial_number 校准单元，其 OTP 地址/长度/位域与候选逐项相同。目标额外 customer_demand 单元位于 OTP 0x22 的高四位，目标 cpufreq 驱动具备解析逻辑。保留目标配套校准表，不盲目覆盖回旧内核数值。目标低温阈值/最低电压、B4 PVTM 分档和 supported-hw 掩码存在差异，完整记录在 analysis/armbian/cpu-opp-audit.json。

已解析配置具备 ROCKCHIP_OPP、ARM_ROCKCHIP_CPUFREQ、NVMEM_ROCKCHIP_OTP、ARM_SCMI_PROTOCOL、ARM_PSCI_FW、CPU_THERMAL、ROCKCHIP_THERMAL 与 step-wise thermal governor。尚需 loader/固件、新内核运行时校准及温控实测；没有改变真机频率或电压。

2026-10-28。当前需求仅Wayland。

## CPU与GPU

只读真机确认I2C0的0x42/0x43分别为RK8602/RK8603，绑定rk860-regulator。原厂cpu@0使用RK806 DCDC2，cpu@400与cpu@600分别使用上述独立稳压器；cpu-supply和mem-supply各自同轨。

f8-pro-compute-power.dtsi保留独立稳压器电压范围550000–1050000uV、斜率2300和休眠约束，恢复三组CPU供电引用。目标基础配置已列REGULATOR_RK860X=y。CPU OPP/PVTM、固件调压和启动行为仍待内核配置及实测。

目标Panthor devfreq代码读取mali-supply，并可选读取sram-supply；当前GPU原厂GPU/内存同接DCDC1。草稿仅补mali-supply，未制造独立SRAM轨，kbase和Panthor两个节点均disabled，后续GPU测试只允许启用其中一个。固件代码要求arm/mali/arch10.8/mali_csffw.bin，仍需取得可信固件并验证。

## loader动态内存

只读运行DT记录见analysis/armbian/live-memory-baseline.json：四段非零内存，含高地址区，MemTotal=12218388KiB。原始厂商board.dtb中没有可直接照抄的DRAM bank节点，loader会插入/回填。不能按“12GB”猜测连续reg范围。

f8-pro-reserved-memory.dtsi保留原CMA 8MiB、ramoops以及原厂占位区；没有复制运行时地址成为静态DRAM配置。vendor-storage运行时占位被回填为0xebc5b000/0x10000，未来必须验证新DTB仍获loader正确修补。vendor-storage驱动在草稿中disabled。

零地址的drm-logo、cubic-lut、vendor-storage保留原厂节点名/占位，带来6条地址/重复地址警告。验证器以原厂DTS重新编译对照，这6条均为继承警告，不隐藏日志。RAM保留区必须在启动前根据实际loader/FIT及DT修补流程再次确认，不能把编译通过当内存布局安全已验证。

## 温控与按键

f8-pro-monitoring.dtsi恢复SARADC参考电源、音量ADC键、原厂TSADC热关断参数120000/CRU/高有效。候选SoC默认极性不同，本机按原值保留。未提高热关断阈值或修改thermal-zone trip；运行时温控仍需实测。DMC补充center与mem电源但保持disabled，避免未验证DRAM固件便启用调频。

## 验证和构建条件

集成编译通过，266项属性读回一致，CPU供电、GPU禁用、图形、PMIC和eMMC引用检查保持通过，无原厂对照之外的新警告。

正在独立WSL目录准备完整固定版本内核源码及签名ARM64 Debian Trixie评估基底。完整Git传输因HTTP/2中断失败，改用固定提交归档和HTTP/1.1按需源码；已下载的逐文件审计输入保留。debootstrap已验证Release签名，包下载/校验尚在进行。Debian基底不是完成的Armbian镜像，尚无Armbian BSP或可刷板级产物。

下一阶段：完成配置解析/编译，检查GPU固件、根文件系统依赖与首启流程；仍需触摸、网络、相机和音频等硬件适配。
