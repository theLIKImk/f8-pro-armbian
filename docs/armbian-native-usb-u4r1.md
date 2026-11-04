# U4r1：USB2 PHY子节点顺序修复（2026-11-01）

最新接续：[U5记录](armbian-native-usb-u5.md)。U4r1的PHY/方向switch/FUSB和自动host/source通过，但U盘无枚举。Windows实测该盘USB2 High-Speed/500mA正常；独立只读status addon在RAM加载，未替换原驱动，升压状态6样本稳定，未测真实电压。临时PHY host无改善已恢复otg。找到同平板USB2-only配置漏rockchip,sel-pipe-phystatus，U5仅补该项已构建待刷；当前仍U4r1在线、U盘插着、自动挂载runtime禁用，电池继续暂缓。

最新实测：U4r1已冷启动，boot_id d83ba29d-2d56-4a09-8240-2bee4bf10466，192.0.2.227。KDE Wayland/Panthor/键盘/背光/原生rw及持久化通过。USB2 PHY实例phy-fd5d0000.syscon:usb2-phy@0.3、orientation switch已注册，otg_mode=otg，顺序修复实机通过。随后insmod退出0，FUSB302/OTG驱动均绑定，0failed，原cannot register tcpm port消失。已临时mask/stop udisks2并保存日志；正等待用户插U盘确认后检查枚举，不能提前标记U盘通过。证据local/hardware/armbian-native-usb-20261101/u4r1/。下方未刷/旧脚本不支持记录已过时；capture-f8-u3-trial.py现支持--revision u4r1，输出已存在禁止重跑。

U4已启动，boot_id ac940394-f7b3-4b6b-a6ba-26d5e34d952c，SSH192.0.2.227，桌面/Panthor/背光/键盘/原生rw持久化通过。已加载同一OTG模块，6-006a绑定成功但6-0022未绑定，deferred为cannot register tcpm port。没有要求用户插U盘，当前不能进行枚举测试。

## 明确的实机差异

local/hardware/armbian-native-usb-20261101/u4/phy01.json显示：PHY平台驱动虽绑定，但没有任何fd5d0000 USB2 PHY实例，otg_mode=UNKNOWN，typec_mux类为空；VBUS regulator disabled/0users，DWC3 device，无Type-C port。结合module-load01.json，FUSB在等待方向接口，不能误认为OTG模块未加载或简单重试insmod。

新增graph节点由fdtput -c插入到兄弟节点最前面。U4 FDT物理顺序为usb2-phy@0下port在先、otg-port在后。参考驱动for_each_available_child_of_node对未知节点goto next_child，但next_child仍++index，num_ports=1时立即break，根本没有创建otg-port。该行为与实机无PHY/UNKNOWN一致。参考完整源码outputs/armbian/firstboot-diagnostic/phy-rockchip-inno-usb2.source.txt的约2582-2620行；未将参考提交声称为运行内核逐字节源码。

此前DT验证逐属性相等不检查兄弟顺序，此处是一个实际顺序依赖；今后在这类端口驱动中增加graph必须检查节点物理顺序。不能仅凭dict相等认定初始化行为相同。

## U4r1改动

基于U4，删除并按原属性重建otg-port，使其位于graph port之前。保留#phy-cells/status/typec-vbus-det/phandle等全部原值，所有引用不变；chosen标记改为u4r1。除标记外所有DT逻辑属性与U4逐项相同，唯一预期行为变化是物理子节点顺序。

新增回归检查读取真实序列化FDT的直接子节点顺序，并模拟num_ports=1驱动遍历：U4实例列表为空，U4r1实例列表恰为otg-port。FIT/resource中DT完全一致，resource SHA1与FIT SHA256、内存边界通过；kernel/ramdisk/模块不变，仍暂存后SSH加载。U4禁止重复刷，已从flash检查白名单撤下。

文件outputs/armbian/official-f8-native-usb-u4r1/BOOT_ONLY_ARMBIAN_NATIVE_USB_U4R1.img，49445820字节，SHA256 f3179f09462038dc9e2c60bce6d00fc149aa3c0e693aa8af41c71f756b771fba。离线通过，冷启动/USB2 PHY实例/方向回调/FUSB绑定/真实U盘枚举均待实测，不把编译检查当硬件通过。

下一步只刷BOOT0x00008000，启动先不接U盘。新SSH先验证chosen u4r1、USB2 PHY实例、otg_mode不是UNKNOWN、方向switch存在、桌面，再临时关闭udisks2自动挂载/保存日志/单独加载模块，确认FUSB绑定后才要求插盘。原capture-f8-u3-trial.py只支持u3/u4，需扩展u4r1并用全新证据目录，不能重跑旧输出。模块路径仍/usr/libexec/f8-pro/f8_otg_vbus_u2.ko，采样按f8_usb_u1=1跳过，电池/充电/高压PD继续暂缓。rootfs与私人备份不重建。
