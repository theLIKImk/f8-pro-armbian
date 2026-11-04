# U4：补USB2 PHY方向/BVALID检测连接（2026-11-01）

最新：U4桌面启动通过，但新增graph port排在otg-port前，参考驱动num_ports=1遍历提前结束；实机确实没有USB2 PHY实例、otg_mode=UNKNOWN、无方向switch，FUSB无法注册TCPM。未要求用户插盘。U4r1只修物理子节点顺序并更新trial标记，已离线完成待刷；见 [U4r1接续](armbian-native-usb-u4r1.md)。当前U4在线，OTG模块已加载但VBUS disabled，不重复加载U4模块或刷U4。

当前实际U3，192.0.2.227，boot_id a262ec8f-29d5-4110-a7f0-f82dc0034611；用户未刷U4。U3实际chosen标记、双向TCPC graph、KDE Wayland/Panthor/键盘/背光/原生p6 rw和持久化通过。单独加载原OTG模块成功，FUSB/VBUS绑定，0failed，采样条件跳过。udisks2运行时mask+停止，临时journal限制32M；重启后runtime mask/配置消失。

## U3得到的实际进展与剩余问题

证据local/hardware/armbian-native-usb-20261101/u3/identity.json、desktop.json、backlight.json、module-load01.json；同级u3flash01.json与u3flipped01.json。

插Type-C U盘后，TCPM host/source，DWC3自动变host，xHCI根hub自动出现，证明U3的角色graph修复实际有效。未人工写DWC3 mode。USB2 PHY extcon USB-HOST=1、USB_VBUS_EN=1，OTG regulator enabled、GPIO4_A6高，但未测量实际输出电压，不能把微伏属性当作电压表。

两种插头方向均没有外设枚举或USB块设备；仅见两个xHCI根hub，不能算U盘通过。首次日志illegal mode/connect-debounce failed，翻转后仍无盘。一次driver-provided otg_mode=host临时试验无改善，finally已恢复otg，未挂载或写盘；证据phy-host01.json。不要重复强制控制器模式或裸寄存器试探。用户只知道普通64GB U盘，品牌型号/USB2兼容性未确认，不归咎于U盘本身。

## PHY证据

原厂otg-port含rockchip,typec-vbus-det，当前A3-U3缺失。当前connector没有方向graph，FUSB probe时三次提示no port node found in connector。参考内核rk3588s-tablet-rk806-single.dtsi明确将u2phy0设orientation-switch并连接usbc0_orien_sw；其现有方向回调调用rockchip_usb2phy_usb_bvalid_enable。参考源码只控制USB2 PHY检测，不翻转未知GPIO，不开启USB3/DP。证据analysis/armbian/usb2-orientation-20261101/audit.json。

已从SHA a67daf71…d0c37b7的实际官方Image按真实System.map反汇编，确认rockchip_usb2phy_orien_sw_set存在并按orientation是否NONE调用BVALID函数；dwc3_usb_role_switch_set实际调用phy_set_mode_ext(USB_OTG=11, role)。实际set_mode接受0/1/6/11，其余会报illegal mode；没有获取当时调用栈，不能单凭这条提示认定根因，也不能承诺新配置一定解决枚举。证据analysis/armbian/official-usb-phy-20261101/。

## U4改动和候选

仅新增USB2 PHY parent orientation-switch、otg-port原厂rockchip,typec-vbus-det及connector port0至USB2 PHY的双向方向graph，chosen f8-usb-trial=u4。U3的TCPC设备节点角色graph不变；与方向graph是两条不同用途的连接。其余DT属性逐项一致；FIT和resource同时更新为同一DT，resource entry SHA1/保留logo与FIT SHA256、内存边界检查通过。

kernel/ramdisk/模块逐字节不变，没有新增自动加载；仍暂存/usr/libexec/f8-pro/f8_otg_vbus_u2.ko，需要启动后SSH独立加载。供电脚/5V500mA PDO/充电参数、A3音频和背光修复保留；仍以f8_usb_u1=1条件跳过电量采样。电池/充电/高压PD适配继续暂缓。

文件outputs/armbian/official-f8-native-usb-u4/BOOT_ONLY_ARMBIAN_NATIVE_USB_U4.img，49445816字节，SHA256 e08b12a7869ea1da940d9a57de743e7854d4d226054122314d21c6aeb6827907。离线通过，冷启动/USB2方向回调/枚举均未实测。

下一步用户先拔U盘、等Type-C退出source，再进入Loader，仅刷boot0x00008000，rootfs不动。启动先不接U盘，SSH核验新boot、chosen u4和两条graph及桌面，然后禁自动挂载/日志/加载模块，再插盘。旧U3脚本固定chosen u3及connector无ports，不适用U4，需新版本/证据目录，不能直接重跑。当前U3 U盘仍插着，PHY临时模式已恢复otg，自动角色host正常、没有挂载。无需重建root或备份。
