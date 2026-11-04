# U3：TCPM设备节点角色连接修复（2026-11-01）

最新实测：U3冷启动/桌面/模块加载通过，插盘后DWC3能自动host，graph修复通过。但两种方向仍无U盘枚举，临时PHY host模式无改善并已恢复otg。已定位缺USB2方向/BVALID连接及原厂typec-vbus-det，U4候选已完成离线校验待刷。见 [U4接续](armbian-native-usb-u4.md)。当前U3在线a262ec8f-29d5-4110-a7f0-f82dc0034611，U盘仍插着，不重复强制模式，不把根hub当U盘通过。

U2已冷启动，SSH192.0.2.227，boot_id 1ca22167-5a98-4f7e-b17c-fec65cd72d5b。实际model/cmdline/DT与U2预期一致；KDE Wayland、Panthor、键盘、原生p6 rw/持久化、正确背光GPIO通过。电量采样按条件跳过，非失败。

## U2运行结果

证据local/hardware/armbian-native-usb-20261101/u2/及同级u2loaded01.json、u2flash01.json。单独insmod成功，6-006a绑定f8-otg-vbus，6-0022绑定typec_fusb302，无新failed单位。/var/log/journal已创建并flush；本次/run/systemd/journald.conf.d/98-f8-usb-u2.conf限制SystemMaxUse=32M/RuntimeMaxUse=8M。原udisks2为active/enabled，试验中runtime mask并停止，防自动挂载；该mask重启消失，不应假定U3启动仍被mask。

用户拔掉原连接并插入Type-C U盘后，Type-C从sink/device变为source/host，FUSB日志SRC_READY与VBUS on，OTG regulator enabled、GPIO134输出高。软件路径供电启用通过，未外接仪表测量真实5V输出电压；不得把regulator microvolts=5000000当作实测电压。DWC3 debugfs仍device，USB设备和块设备均空，自动角色切换未通过。

内核提示OF: graph: no port node found in /i2c@fec80000/fusb302@22。本地6.1参考tcpm.c的tcpm_register_port使用usb_role_switch_get(port->dev)，从FUSB302设备节点找graph；U2将端点放在connector子节点，导致USB role switch未连接。此源码是参考提交而非逐字节官方源码，但与实际错误和角色未传播相符。

仅做一次临时DWC3 debugfs mode=host试验：xHCI根hub出现，但没有U盘，日志phy illegal mode、connect-debounce failed。未挂载/写入任何块设备。试验finally已恢复mode=device；Type-C仍source/host、U盘仍插着，供电由TCPM管理。debugfs直接切换未走role-switch回调中的phy_set_mode_ext，不能作为完整PHY切换。不要再重复强制host或手动翻GPIO。

## U3候选

将唯一FUSB USB2角色端点从/i2c@fec80000/fusb302@22/connector/ports/port@0/endpoint移到/i2c@fec80000/fusb302@22/port/endpoint。保持端点phandle与对端引用，删除空的connector/ports子树；chosen新增f8-usb-trial=u3。其余DT属性逐项完全一致，包括USB2速度、5V500mA PDO、OTG/中断脚、音频MCLK、背光与充电参数。将同一新DT同步写入FIT/resource，重新校验resource文件SHA1、FIT SHA256和内存边界。kernel、ramdisk、模块原样，两个logo原样。

文件outputs/armbian/official-f8-native-usb-u3/BOOT_ONLY_ARMBIAN_NATIVE_USB_U3.img，49445036字节，SHA256 5ccccc72e7536d2825279961b7f434be018aeeabfae8aaf13b0cb20082124e46。离线通过，冷启动/自动角色/真实U盘枚举均未验证。

仍暂存模块/usr/libexec/f8-pro/f8_otg_vbus_u2.ko，不自动加载，不在init中insmod。沿用f8_usb_u1=1采样条件跳过。U3启动后先SSH确认chosen标记和新端点，再重新runtime禁用自动挂载、保存日志并单独加载同一模块；然后让用户插U盘，检查TCPM与DWC3/PHY是否一致及实际枚举。旧load脚本硬编码U2 boot_id且证据已存在，禁止直接重跑，要用U3新脚本/新证据目录。

用户下一步：先拔U盘，等Type-C退出source，再进入Loader；只刷boot0x00008000，不动rootfs。启动后先不插盘，待SSH检查。当前尚未刷U3，仍U2在线；不再要求回A3才能测试，但若整体异常可只刷A3恢复采样。电池工作继续暂缓。不要重建完整root或私人备份。
