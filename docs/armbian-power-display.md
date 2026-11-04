# F8-PRO 单 RK806 与显示草稿

2026-10-28。本轮仅本地静态分析和设备树编译，没有改动真机。

## 电源审计

锁定内核提供 rk3588-rk806-single.dtsi。对原厂 21 路 DCDC/PLDO/NLDO 的电压约束、启动开关、斜率及休眠状态逐项比较，19 路完全一致，另外两路差异为：

- DCDC_REG2：候选额外指定 regulator-init-microvolt=800000，原厂没有此属性，草稿删除。
- DCDC_REG3：候选 regulator-max-microvolt=800000，原厂为750000，草稿保留750000。

完整差异见 analysis/armbian/power-rail-comparison.json；工具 tools/audit-f8-power.py。比较的是设备树约束，不能推断当前寄存器实际电压或实际休眠行为。

armbian/dts/f8-pro-power.dtsi 引入官方单 PMIC 定义并覆盖上述两处，补充原厂5V、1.1V固定供电和面板电源。面板电源链为 DCDC_REG8（3.3V）→GPIO4_A3控制的vcc3v3-lcd0-n→面板；复位为GPIO1_B0，背光为PWM14、GPIO1_C4使能。面板电源暂禁用。

上游单 PMIC 定义还不能整体认定为本机最终适配：PMIC pinctrl、关机管脚、SoC电源消费者、运行时调压及休眠唤醒均须继续检查。当前编译包装不是可启动板级配置。

## 显示草稿

armbian/dts/f8-pro-display.dtsi 保留原厂面板完整时序、延迟、尺寸、4条DSI lanes、格式和flags，使用符号引用连接DSI0与面板。保留160MHz、1200×1920及原始porch/sync参数；没有编造初始化命令。单端口图形节点改用无地址的port结构。

面板仍disabled，DSI/PHY/VOP/显示路由、供电启动顺序以及Panthor与显示导入的联合验证尚未完成。根文件系统、启动、eMMC和固件也不在这个编译包装的覆盖范围。

## 验证

tools/validate-armbian-peripheral-dt.py 编译纯SoC对照与集成草稿，读回原厂稳压器约束/休眠参数、面板时序和原有15项外设参数。最新执行结果与警告差异保存 analysis/armbian/dt-validation/validation.json，编译产物明确标注DO-NOT-FLASH。

下一步先对照PMIC pinctrl和电源消费者，再补DSI0的PHY、VOP和显示路由，之后准备完整内核配置、启动与恢复验证。

本轮验证：177项原厂属性读回一致，SoC43条警告、集成41条，新增0。
