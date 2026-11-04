# U5：USB2-only PIPE状态选择（2026-11-01）

最终验收覆盖下方待刷记录：U5 USB2存储完整枚举/容量/只读exFAT访问通过，原生root已安装开机服务，真实重启后自动加载通过，用户确认文件管理器可见分区并打开文件。当前boot3f9b409e-0860-438a-a5eb-2ac768dbafd2，192.0.2.227，U盘仍插着且桌面已挂载；udisks恢复正常。详 [U5成功与持久化记录](armbian-native-usb-u5-success.md)，无需再刷镜像，不重新运行旧手动load脚本。电池仍暂缓。

当前仍U4r1，SSH192.0.2.227，boot d83ba29d-2d56-4a09-8240-2bee4bf10466。用户尚未刷U5。U4r1桌面/Panthor/键盘/背光/原生rw持久化、USB2 PHY实例、方向switch、FUSB/OTG绑定与自动host/source均通过，但U盘仍没有枚举。phy-host临时试验无改善，finally已恢复otg。U盘目前插回平板、host/source，udisks2仍runtime mask，未挂载或写U盘。

## 本轮排查改变了哪些判断

1. U盘接Windows实测正常：USB DISK/USSD，VID:PID 152d:0583，容量63869299200字节。用Windows原生USB hub只读descriptor IOCTL得到bcdUSB=0x0210、Speed=2(High-Speed)、配置500mA、Mass Storage/SCSI/Bulk-only(08/06/50)。这只盘已经实际以USB2高速工作，不能继续把问题归因于未知USB2兼容性。未读取用户文件或磁盘扇区，没有通过VID/PID就断言真实芯片型号。证据pc-usb-descriptor01.json，API依据[Microsoft USB descriptor query](https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/usbioctl/ni-usbioctl-ioctl_usb_get_descriptor_from_node_connection)。枚举其余hub有一项不支持查询，不影响目标设备返回的完整descriptor。

2. 尝试RAM替换控制模块以增加只读状态：首次因平板仍有Type-C partner在前置断言停止，无任何远端变更；用户确认平板USB口完全空后，正常rmmod被内核以module in use拒绝，未force。原模块从未成功移除，FUSB已恢复绑定。编译出的13560字节diagnostic替代模块未加载，不能将其当成当前驱动。

3. 改用独立只读addon f8_otg_status.ko，9480字节SHA d4a6c85f139de0a496d6a82380df3af44ef5ced408bf7450eac3be373e5a69c3，16符号与实际官方内核/模块CRC匹配。已从/run/f8/passive-usb-status01/加载，未替换原控制驱动；它持有原模块引用并只提供/sys/bus/i2c/devices/6-006a/f8_usb_status/status。通过已绑定I2C client读REG00/02/03/07/0A/0B/11/14，完全没有配置写入、ADC启动或0C故障锁存读取。原控制模块仍a61fdb4c…556b39c。addon只在RAM，重启消失，不在U5里；不要force卸载原模块。

4. 用户安全移除电脑U盘并插回平板后，同boot连续6个样本5秒完全一致：REG03=0x30、REG0B=0xe2(VBUS_STAT=7)、REG0A=0x75、GPIO134高，TCPM host/source、DWC3 host。与未插时REG03=0x10比只有OTG位变化，其他采集配置相同。软件升压状态稳定，但未测真实端口电压，REG11是cached ADC，不能当作新鲜电压或排除电气问题。证据u4r1/status-addon01.json、source-status01.json。

5. 只读debugfs：USB2 GRF0x10=0xf、UTMI0xc0=0xbe2，DWC3 GUSB2PHYCFG0=0x00101448。原USB2-only路径未注册/使用usbctrl GRF的PIPE状态选择。一次在已具备BVALID的U4r1上临时PHY host仍没有盘，已恢复otg；与U3不同前置条件有记录，但不能反复盲试该接口。

## 找到的配置遗漏

参考提交85233a85…中rk3588s-tablet-rk806-single.dtsi完整USB块与我们一样：DWC3 otg、high-speed、phys仅u2phy0_otg、phy-names usb2-phy、usb-role-switch，USB2 PHY orientation-switch/typec-vbus-det。它额外在u2phy0_otg设置rockchip,sel-pipe-phystatus。该属性前轮遗漏；驱动在PHY init时通过rockchip,usbctrl-grf选择PIPE phystatus来自GRF，适用于USB3 PHY未启用的这条USB2-only配置。实际官方Image含该属性字符串，参考实现与同平板完整块已保存于analysis/armbian/usb2-only-20261101.json和U5输出reference-tablet-usb2-only.dtsi.txt。参考提交不是已证明逐字节运行源码，实机效果仍需测。

## U5候选

只给/syscon@fd5d0000/usb2-phy@0/otg-port新增rockchip,sel-pipe-phystatus，并更新chosen标记u5。其他DT属性逐项相同，保持otg-port排在graph port之前；两条角色/方向graph保留，FIT/resource DT一致。kernel、ramdisk、原OTG模块、充电参数、5V500mA声明和A3音频/背光均不变。仍不自动加载模块，采样仍按f8_usb_u1=1条件跳过。

文件outputs/armbian/official-f8-native-usb-u5/BOOT_ONLY_ARMBIAN_NATIVE_USB_U5.img，49445856字节，SHA256 9044ece30ff5806f975f9030b49dab8f8bed38226bce9385381dee5708c5e237。离线FIT/resource哈希、逐属性diff、节点顺序与内存边界通过，冷启动和U盘枚举尚未通过。已完成构建，不重复运行。

下一步先拔U盘，进入Loader，只刷boot0x00008000，不动rootfs。启动后先不接盘；新SSH核chosen u5、PHY/方向接口、usbctrl GRF映射与PIPE字段、桌面，再runtime禁自动挂载/日志/单独加载原模块，最后插U盘。需要扩展现有capture-f8-u3-trial.py revision u5，不能直接重跑旧u4r1证据；被动addon不是启动必需，不要自动重跑卸载模块的失败步骤。若失败，只刷回U4r1或A3，不恢复整个root。电池/充电/高压PD适配仍暂缓，别改充电门限。
