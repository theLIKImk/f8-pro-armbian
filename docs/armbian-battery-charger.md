# 电池曲线与充电策略适配

2026-10-29。新增 f8-pro-battery.dtsi 只保存禁用草稿，未启动充电驱动或改写平板。

CW2015 的64字节电池曲线逐字节保留原厂内容，监测周期2000ms，power-supplies引用本机BQ25890。目标驱动按u8数组读取并要求恰好64字节，原厂16个32位大端cell编译后的原始字节满足接口。目标驱动在初始化中可能写电池曲线，静态一致不能代替真实电池/现有寄存器验收；因此节点保持禁用。

BQ25890 的地址、中断、OTG GPIO和全部原厂数值参数均迁移到禁用节点。设备树集成检查增至318项，通过且没有原厂对照之外的新警告。目标模块编译通过不代表板级充电策略兼容。

目标驱动读取7个必需和3个可选u32属性，未读取原厂 ti,max-input-voltage、ti,max-input-current、ti,max-charge-voltage、ti,input-current 及 SDP/DCP/CDP 分档。原厂同时给出 max-charge-voltage=4200000 和 battery-regulation-voltage=4400000；目标只读取后者，原厂最终有效策略仍须核清，不能直接启用。PD worker又把协商电流分别转换为输入限流与充电电流，尚没有按本机原厂上限约束的迁移。审计见 analysis/armbian/charger-policy-audit.json。

原厂 extcon 和 otg-mode-en-gpios 不由目标驱动直接读取。目标提供 usb-otg-vbus regulator，并在获得 legacy USB PHY 时跳过 regulator 注册；这与原厂 regulators/vbus5v0-typec 及FUSB302引用不同，草稿没有将旧regulator子树伪装成已可用接口，也暂未接入 ti,usb-charger-detection。FUSB302/TCPM电源供应具有目标通知代码需要的 CURRENT/VOLTAGE NOW/MAX 属性，但仍需处理通知、PHY、OTG使能和角色切换的完整链路。

原厂 charger_ok pinctrl 指向 GPIO0_D5，interrupt-parent/interrupts却指向 GPIO3_D5。只读现场确认 Linux IRQ136/hardware line29 名称bq25890_irq，列表未给GPIO bank，不能据此猜测修正；sysfs设备没有irq属性。GPIO134（GPIO4_A6）由otg-mode-en申请，观测为输出低。此证据保存于 analysis/armbian/live-charger-irq-2026-10-29.json。

另只读获取旧驱动公开属性：constant_charge_voltage_max=4400000、constant_charge_current_max=2496000、input_current_limit=2750000、charge_term_current=64000，快照见 analysis/armbian/live-charger-properties-2026-10-29.json。constant_charge_voltage=4244000 不能作为终止电压证据；目标驱动对此属性读取F_BATV ADC，而MAX属性取初始化配置值。旧驱动实现仍未完整核清，观测没有替代充电策略适配；没有执行sysfs写入或原始I2C读写。

还发现原厂FUSB302 connector/ports/port@1含remoteAudioService.java-endpoint，而非标准remote-endpoint。不得直接复制这一异常名称成为目标USB-C graph。下一步先查清原驱动充电限制与IRQ实参，再适配限制解析及PD通知、FUSB302/VBUS/USB PHY图；充放电、电量读数、插拔、PD和OTG均未在新内核验收。
