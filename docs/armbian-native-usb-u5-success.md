# USB2存储接入与开机自动加载验收（2026-11-01）

U5 USB2存储接入通过。用户在实际重启后确认“能看到分区并打开文件”；SSH复核usb-storage/480Mb/s、64GB盘及分区、exFAT已由桌面正常挂载，系统0failed。

## 当前真实状态

- 当前BOOT：outputs/armbian/official-f8-native-usb-u5/BOOT_ONLY_ARMBIAN_NATIVE_USB_U5.img，49445856字节，SHA256 9044ece30ff5806f975f9030b49dab8f8bed38226bce9385381dee5708c5e237。
- 当前boot_id：3f9b409e-0860-438a-a5eb-2ac768dbafd2，IP192.0.2.227，f8test，严格固定公钥SSH。原生p6 ext4 rw，KDE Wayland正常。
- U盘仍插在平板上，host/source；VID:PID 152d:0583，USSD，USB2 480Mb/s，usb-storage绑定。sda 124747769个512字节扇区（63870857728字节）；sda1为exFAT主分区，sda2为32MiB FAT分区。Windows WMI容量按几何信息约63.9GB，与实际扇区容量有小差异，非据此判断坏盘。
- 用户已在文件管理器打开文件，sda1由正常桌面挂载为rw，uid/gid1601。原先udisks2的runtime mask已随重启消失，当前active/enabled。不要再禁用或卸载用户正使用的盘。
- 没有执行写入测试、fsck、格式化或修改用户文件。此前只读块读取4096字节、exFAT ro挂载/目录元数据检查后正常卸载均通过；正常桌面挂载后的OS元数据行为不能被描述为“保证U盘完全没有写入”。
- 电池/充电/高压PD适配仍暂缓。f8-live-power因f8_usb_u1=1条件跳过，保持现有充电参数。USB3/其他外设/电脑日志盘双向切换未完整验收，不把USB2存储通过扩大为全部USB功能完成。

## 修复组合及证据

保留A3音频MCLK及背光PWM14m1修复；USB加入FUSB302和仅OTG的VBUS regulator；角色graph位于FUSB设备节点；USB2 PHY方向/BVALID graph与typec-vbus-det已接入；物理otg-port必须排在graph port之前，避免单端口驱动计数提前结束；U5补充rockchip,sel-pipe-phystatus，与同平板USB2-only参考配置一致。FIT及resource两份DT保持相同。

U5 cold boot 9df01d2b-d624-4364-8d3d-a06ff6847720：正确DT/PIPE选择0x0189/PHY/方向switch/桌面通过。单独加载模块后插盘，首次完整枚举成功，usb-storage已注册sda。storage01.json核对容量/分区及只读4096字节读取；exfat-readonly01.json验证ro,nosuid,nodev,noexec挂载与目录访问后卸载，没有输出用户文件名或内容。

随后用户拔盘，已核对Type-C partner消失、VBUS disabled、USB文件系统未挂载，再安装原生根上的开机服务。真实systemctl reboot后新boot_id为3f9b409e…，服务日志明确module_already_loaded=false，证明由服务在新启动中自动加载，没有重做SSH热补丁。FUSB/OTG绑定、Wayland、0failed、空口VBUS disabled通过。再插同盘自动枚举、桌面文件访问得到用户与SSH双重确认。

证据均在local/hardware/armbian-native-usb-20261101/u5/，特别是startup-install01.json、reboot-request01.json、reboot-verification01.json、post-reboot-usb01.json、user-acceptance01.json；初次USB枚举在同级u5flash01.json。

## 原生根持久化配置

armbian/usb/usb-otg-start.py安装至/usr/libexec/f8-pro/usb-otg-start.py，SHA670b3e0ef5af346aadc212b6a27b801061903c2054cca3a7063a65c9552f70b0。

armbian/usb/f8-usb-otg.service安装至/etc/systemd/system/f8-usb-otg.service，SHA0eb23f0357bca05c18fc02c1dce9280ea5d6faa05217e152d0fcc49e976a8fe2，并启用至f8-desktop.target.wants。oneshot/RemainAfterExit，After准备、SSH和SDDM，无Requires将USB成功设为桌面条件。helper只允许已验证u5 DT/固定kernel/模块hash，先检查采样条件跳过及PHY，再加载暂存原模块并确认两驱动绑定。当前active/exited/success。

原模块仍a61fdb4cd70d8c60b53341f53e818b7ac0318d8798a92a1cf22c34e12556b39c，从BOOT暂存到/usr/libexec/f8-pro/f8_otg_vbus_u2.ko。开机服务属于当前原生可写root的持久化变更，U5 BOOT本身并不安装这两个新服务资产；后续重建rootfs时必须集成runtime-integration.json所列文件及启用关系，不能只复用BOOT后声称自动加载仍在。

回退A3没有f8_usb_u1=1，USB服务条件跳过、原采样服务恢复。未来改USB profile marker时需更新helper准入并测试；以U5为基础的其他非USB适配可保持USB profile=u5。不要在新启动中重跑旧baseline收集器，它要求模块未加载；不要重跑旧硬编码boot_id的load/deploy脚本。

U4r1期间的f8_otg_status只读addon已随重启消失，此次U5通过没有依赖它。另一个诊断替代驱动从未成功替换，rmmod曾拒绝in-use，无force。不要把该未加载候选打入正式根或启动资产。

当前无需再刷BOOT/rootfs或重复备份。保留U5和当前root配置作为后续非电池硬件适配基线。日志persistent目录此前为硬件取证创建，测试用32M journald override仅在/run，重启后不再生效；没有添加长期后台监控。
