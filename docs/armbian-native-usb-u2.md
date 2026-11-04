# U2：统一引导设备树，延后USB模块加载（2026-11-01）

最新实测：U2冷启动/桌面/SSH/正确DT通过；同boot单独加载OTG模块成功，Type-C直插U盘后source/host、VBUS enabled，但DWC3仍device，未枚举。一次临时host测试出现xHCI根hub但PHY illegal mode，已恢复device，未挂载/写盘。U3只修角色graph位置并保持FIT/resource同步，已构建待刷；见 [U3记录](armbian-native-usb-u3.md)。当前仍U2在线，模块已加载，U盘仍插着；runtime禁用了udisks2，重启会消失。

用户已按回退说明启动，SSH192.0.2.227身份通过，boot_id ff811d06-5d9a-48ae-b204-98e7e102666d。运行命令行与A3一致，无f8_usb_u1标记；f8-live-power正常active，0failed，U1 dropin不存在，说明留存失败启动未运行到安装该文件的阶段。用户尚未刷U2。

## 失败日志及结论边界

取证local/hardware/armbian-native-usb-20261101/u1-after-rollback01.json和u1-full-pstore01.json。journal未持久化，只有当前启动，前次journal不存在；完整pstore console为51594字符。保存的失败启动使用官方6.1.115内核和原生测试init，但Machine model为Rockchip RK3588S TABLET V11 Board，command line为原厂rootwait/PARTUUID/ttyFIQ0形式，缺少systemd.gpt_auto=0和原生根UUID。init于4.558606秒报gpt-auto-policy并停等，未进入root挂载或insmod阶段。留存记录没有U1特有标记，所以不能仅据它证明每次黑屏都同一原因；也不能把此次失败归为OTG驱动崩溃或ABI错误。

离线核对U1 FIT内DT仍有正确A3 model/启动参数、GPU/背光修复及U1 USB节点，FIT配置与A3仅timestamp变化；但multi/resource负载一直沿用原厂，内嵌rk-kernel.dtb保留原厂model、GPU及启动参数。留存失败记录符合该原厂树的特征。引导器选择了何处DT的确切分支尚未从串口证实；U2消除两个DT来源不一致，并分离驱动加载测试。

## U2改动与校验

U2基于U1，kernel与FIT fdt逐字节不变；将resource中的rk-kernel.dtb替换为与FIT fdt完全相同的DT，重新计算resource的SHA1、长度及512字节块偏移，保留两个logo文件原字节。重读三个序列化entry校验哈希和内容，FIT所有负载SHA256及FDT/ramdisk内存边界通过。

initramfs取消insmod，只将原ABI已核验的f8_otg_vbus.ko暂存为/usr/libexec/f8-pro/f8_otg_vbus_u2.ko，不自动加载，没有USB模块成功的桌面依赖。模块仍是a61fdb4c…556b39c，与通过149项离线控制测试的源码一致。

保留f8_usb_u1=1标记，U2启动仍条件跳过f8-live-power采样以避免后续OTG试验争用。充电初始化/充电参数不改，A3回退无标记时自动恢复采样。USB2/5V500mA声明保持，电池/高压PD仍暂缓。FUSB在VBUS provider模块未加载前预期deferred，不能把这一点当成新失败，也不应在此阶段宣称U盘支持已通过。

文件 outputs/armbian/official-f8-native-usb-u2/BOOT_ONLY_ARMBIAN_NATIVE_USB_U2.img，49445072字节，SHA256 891f3ee912dda91aad9d6a795b06f5e2c611e6488cffab6840e99bacc9be3b5f。离线通过，cold_boot_verified=false、usb_flash_enumeration_verified=false。构建已完成，不重复运行。

## 实测顺序

先拔U盘，只刷BOOT地址0x00008000，不动rootfs/Loader/recovery/分区表。启动后先让用户确认桌面与IP，再SSH核对实际model、cmdline、GPU/背光、root rw和FUSB deferred状态；此时不应已加载f8_otg_vbus。旧logo文件保留，可能依旧短暂出现，不能据此判断加载的系统。

桌面/SSH通过后，先保存新基线和启用有限持久日志，禁止桌面自动挂载，检查外部源未接及module文件哈希，再通过SSH单独加载暂存模块并收dmesg/driver/role状态。最后用户插U盘，检查host/source、枚举及容量，只读、不格式化不写入。若启动仍失败，只刷回A3，再保存新pstore，用新编号，不能覆盖第一次证据。
