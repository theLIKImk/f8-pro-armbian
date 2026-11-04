# USB 外设适配 U1：诊断完成，修复未部署（2026-11-01）

最新覆盖：A3已恢复并取到完整pstore，留存失败因缺少gpt-auto-policy启动参数在模块加载前停止，使用原厂model/参数，与U1 FIT DT不一致。已准备U2统一FIT/resource DT并取消early insmod，见 [U2接续](armbian-native-usb-u2.md)。当前A3在线，U2待刷，U1仍停用。

## 最新实机失败：停止使用U1

用户已刷U1，反馈旧logo闪过后一直黑屏。主机只见C/D无日志盘，SSH尝试Connection closed、尚未认证，因此不能认定内核/systemd已成功运行。U1 preflight标记失败，已撤出check-flash-file白名单，勿重复刷入。先只刷回已验证A3（boot0x8000，rootfs不动），先不接U盘，待用户确认恢复后运行tools/capture-f8-u1-failure.py收集前次journal、pstore及U1条件dropin。回退尚未确认。

U1 initramfs中insmod失败会进入fail停等，可能阻断桌面/SSH，但目前没有日志证明具体原因；GPIO/角色/模块异常均不能排除。后续修订必须将USB试验移到可记录、可超时/可回退的系统启动后阶段，避免把外设模块失败设为基本桌面的必需条件；先取证，不能只据ABI通过认定驱动能实机运行。旧logo可能来自此前保留的bootloader/resource显示，单凭该画面不能判断启动了Arch或分区被回写。

## 最新：U1已生成，待实机启动

BOOT文件 outputs/armbian/official-f8-native-usb-u1/BOOT_ONLY_ARMBIAN_NATIVE_USB_U1.img，49431040字节，SHA256 df96bbd614f36daa1e338a525271114a5ba7e387817869151116b6d9ea3cba98。Windows文件校验PASS，FIT各负载与内存边界通过。只刷boot 0x00008000，不动rootfs/分区表/Loader/recovery。用户尚未刷U1；当前仍A3在线。

已确认原厂GPIO0_C4中断和GPIO4_A6 OTG门控；A3实机两脚均未占用，证据prerequisites01.json。新增armbian/usb/f8_otg_vbus.c专用I2C regulator，仅识别地址6a/PN3、要求现有watchdog关闭，启动时不重置芯片、不初始化充电参数、不注册充电power_supply、不接充电IRQ。FUSB302通过regulator控制供电时仅改变REG03的OTG_CONFIG及GPIO4_A6；检测输入电源或非5V附近boost配置时拒绝开启，关闭/移除/关机尝试关闭OTG。I2C关闭失败也先拉低门控。不回写自清零watchdog-reset位。此寄存器/OTG脚组合依据[TI BQ25890数据手册](https://www.ti.com/lit/ds/symlink/bq25890.pdf)及原厂DT；实际芯片兼容性/输出波形仍待实机。

模块12184字节，SHA a61fdb4cd70d8c60b53341f53e818b7ac0318d8798a92a1cf22c34e12556b39c；17个导入符号CRC与实际26.8.1官方模块/内核全部匹配。rdev_get_drvdata未被随附模块引用，因此从实际官方Image的并列ksymtab/kcrctab读取；地址映射已用其余16个独立模块CRC交叉验证，不是用头文件自证。证据outputs/armbian/official-f8-usb-u1-module/actual-official-abi.json。实际C控制函数通过149个假芯片测试，覆盖位保留、输入存在拒绝、输出配置异常、I2C失败门控关闭和watchdog strobe，control-tests.json已保存；编译与模拟通过不等于硬件通过。

U1新增FUSB302、fcs,int_n-gpios和USB2双向graph；DWC3改otg+usb-role-switch，默认peripheral，仍high-speed。只声明5V/500mA source/sink PDO，不开启USB3/DP/高压PD。原厂有缺陷的remoteAudioService.java-endpoint不复制。A3音频MCLK和背光修复保留，kernel/resource原样。

U1内核命令行增加f8_usb_u1=1；initramfs加载专用模块，并安装f8-live-power.service.d/98-f8-usb-u1.conf，ConditionKernelCommandLine=!f8_usb_u1=1，避免原I2C/ADC采样与内核驱动争用。仅U1下跳过电量采样，状态页电量可能缺失/不刷新；充电配置不改。回退A3不含该命令行参数，原服务自动恢复，无需手工恢复充电参数。USB日志gadget仍保留设备模式能力，实际host/device切换与日志导出待测试。

首次刷入前先拔U盘，启动联网后先SSH核对新boot_id、模块绑定、FUSB/role/vbus状态，预期电量采样服务为条件跳过而非active，不能原样运行强制要求f8-live-power active的旧桌面验收脚本。插盘前临时禁止桌面自动挂载（只读核对或暂停udisks服务并记录原状态），再让用户插入Type-C U盘，查看host/source、USB枚举与块设备容量。只读检查，不自动写入/格式化。异常BOOT-only回退A3，勿回旧背光有缺陷版本。U1 cold_boot_verified和usb_flash_enumeration_verified仍false。

以下为此前诊断阶段记录，尚无U1的表述已被本节覆盖。

用户将USB外设接入调整为当前优先项，当前插着Type-C U盘，直接连接，没有转接头或外部供电扩展坞。当前A3在线192.0.2.227，boot_id b6220a3a-0022-436d-bb1d-0210a2782bdf。扬声器短音已通过；默认音频路由工作暂后移。电池电量/充电/高压PD适配仍暂缓；本轮只读，没有USB角色、GPIO、BQ或PD寄存器写入，没有写U盘。

## 实机证据

local/hardware/armbian-native-usb-20261101/initial01.json：

- DWC3 fc000000.usb绑定，但运行DT dr_mode=peripheral、maximum-speed=high-speed，仅USB2 PHY。
- UDC绑定f8_official_desktop_t1 mass_storage.0日志盘功能；usb_role、typec类为空，没有USB主机根hub，lsusb -t为空，U盘尚未枚举。
- USB storage、UAS、HID驱动均已注册，不能归因于缺U盘文件系统或挂载工具。
- 其他EHCI/OHCI/USB host控制器均disabled；只启用它们不能证明它们接到此Type-C口。

这是此前日志盘诊断保留的固定设备模式，不能当作已经支持OTG。

## 原厂与源码核对

analysis/armbian/usb-a3-factory-dt-20261101.json由实际A3 FIT和原厂Ubuntu board.dtb解析，禁止直接搬运原厂phandle数字。

原厂DWC3为otg并有usb-role-switch及connector graph。原厂I2C6 fusb302@22，fcs,fusb302，中断GPIO0_C4低电平（interrupt-parent实际phandle还需映射核对），vbus-supply指向charger@6a/regulators/vbus5v0-typec。原厂charger还有GPIO4_A6 otg-mode-en控制。原厂connector port@1有异常remoteAudioService.java-endpoint，不复制为有效graph。

官方镜像kernel.config确认USB_DWC3_DUAL_ROLE=y、TYPEC_TCPM=y、TYPEC_FUSB302=y，但CONFIG_CHARGER_BQ25890未启用。当前A3不含FUSB302节点及其VBUS regulator。仅把dr_mode改host无法补上Type-C接入检测及U盘供电。

analysis/armbian/usb-source-20261101/保存本地6.1参考源码及上下文。FUSB302 set_vbus通过regulator_enable/disable控制vbus，devm_regulator_get要求真实VBUS提供者。参考BQ驱动提供usb-otg-vbus接口，但若找到legacy USB PHY则跳过注册，且原厂otg-mode-en属性并未被该驱动直接消费。参考源码属于85233a85…，尚未证明与运行6.1.115逐字节相同，不能直接编译后声称ABI兼容。

## 修复所需工作

1. 核对运行6.1.115对应头文件/模块ABI与Type-C驱动的graph绑定；解析实际GPIO phandle和占用，确认FUSB中断及OTG GPIO。
2. 实现受Type-C角色控制的5V OTG电源接口，保留现有充电参数，处理拔出/关机关闭和与遥测I2C锁的协调。不得直接加载会重置或重设充电参数的通用BQ驱动；不得用dummy regulator假装U盘已有电源。
3. 从A3增量生成U1：补FUSB/正确双向graph，DWC3改otg+role-switch，先保持USB2，保留A3音频/背光、原生root和Wi-Fi SSH。日志盘服务需兼容host角色，不再固定占用端口。
4. 离线检查通过后只刷BOOT实测：Type-C host/source角色、5V源供电、xhci根hub、U盘枚举、只读查看容量/分区及用户确认，随后拔出恢复角色。不要自动挂载写入或格式化U盘。恢复设备模式时验证电脑日志盘功能。

目前没有可刷U1镜像，不要求用户重刷A3、不将诊断写成修复完成。当前U盘保持直连即可，后续采样用新编号，不覆盖initial01。
