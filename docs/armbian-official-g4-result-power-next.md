# G4 实测通过，转向供电适配（2026-10-29）

用户确认触摸工作、GPU确实驱动。F:卷标F8AG4的40份白名单日志已保存到local/hardware/armbian-official-g4-20261029-01，test-result.json记录证据和文件哈希。触摸事件2257条、按下19次、最大同时2个触点；GPU Panthor/Mesa硬件像素读回通过。G4 preflight已加实测通过并保留before-hardware副本。全桌面、长期稳定性和充电未验收。

用户希望优先处理供电，提供充电器输出5V/3A、9V/2.22A、12V/1.67A。仅凭铭牌不认定具体快充协议。已告知先准备5V测试，高压协商后续适配。用户随后询问能否先回原BOOT：已答复可以，日志已安全保存，回原系统后按原方式充电；尚未收到实际回退完成确认。

## 已核对的供电问题

- I2C6仍误用m0，原厂为m3 GPIO4_B0/B1（bank4 pin8/9），需要像G4修触摸一样逐项核对并修正。
- BQ25890与CW2015节点在试验镜像中禁用。原厂4.2V max-charge-voltage与4.4V battery-regulation-voltage冲突，新驱动不解析部分原厂输入限制/充电分档；不能直接启用旧草稿。
- 充电IRQ原厂pinctrl GPIO0_D5与interrupt-parent GPIO3_D5矛盾尚未解决；OTG GPIO4_A6、FUSB302/VBUS/USB PHY的角色链路仍待适配。
- 精确官方26.8.1内核CONFIG_I2C_CHARDEV=y、TYPEC_TCPM=y、TYPEC_FUSB302=y；实际power/supply模块目录只发现nanopi_adc_power.ko，未发现配套BQ25890/CW2015模块。旧extra-modules不能假定适配官方26.8.1，需重做实际导入CRC核对。
- TI BQ25890资料说明REG0C故障寄存器读取会影响锁存记录，下一版只读诊断应跳过此寄存器。资料：https://www.ti.com/lit/gpn/bq25890 。已有本地CW2015源码电压换算采用avg*312/1024毫伏，不能混用其他芯片的312.5微伏比例。

## 下一步

先准备以G4为基线的供电诊断：恢复原厂I2C6 m3、保持标准充电/电量计驱动禁用，利用内置i2c-dev定点读取BQ/CW状态与配置（不扫描总线、不改寄存器值、不触发ADC转换/复位/PD/OTG，不读取会清锁存的故障寄存器）。读取前核对物理bus路径及无驱动绑定。将有效寄存器配置、CW曲线与原厂归档对比，查清限制后再接入5V充电控制及power_supply。该诊断代码和G5镜像尚未生成；本轮仅完成供电前置检查，无硬件供电写入/新部署/后台任务。

回退文件：outputs/armbian/firstboot-diagnostic/CURRENT-BOOT-ROLLBACK-64MiB.img，SHA256 7e51e71f7ec7439357e5ea2fbb97118715fe5fcf10401b638609df33567b1dd1。仍只刷boot，起始LBA0x00008000。
