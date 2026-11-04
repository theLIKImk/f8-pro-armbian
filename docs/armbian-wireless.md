# F8-PRO 无线与 RTC 适配草稿

2026-10-29，仅本地源码/DTB 核查，没有无线复位、固件上传或真机配置变更。

新增 armbian/dts/f8-pro-wireless.dtsi，基于原厂 board.dtb 恢复 AP6275P 的 wlan-platdata、PCIe2x1l2、UART9 蓝牙平台节点和 HYM8563 RTC 时钟引用。全部相关外设及 PCIe PHY 保持 disabled，不能用于启动或网络功能验收。

Wi-Fi 使用 pcie@fe190000 → phy@fee00000（combphy0_ps），单通道、最高 Gen2；PERST 为 GPIO3_D1，平台电源 GPIO0_C7，主机唤醒 GPIO0_A0。保留 rockchip,skip-scan-in-resume 和 PCIe 默认 pinctrl 的 Wi-Fi 电源上拉。没有复制其他开发板额外 PCIe 电源或将 AP6275P 改成 SDIO。

蓝牙使用 UART9 m2，RTS 为 GPIO3_D2，复位 GPIO0_D4、设备唤醒 GPIO0_C6、主机唤醒 GPIO0_C5。保留原厂默认/RTS GPIO 两种 pinctrl 状态。外部时钟来自 I2C6 0x51 的 HYM8563；RTC 中断 GPIO0_B0 低电平，输出 32768 Hz。RTC 因尚未运行时验收也保持禁用，后续不能只启用蓝牙而遗漏其时钟提供者。

目标源码 net/rfkill/rfkill-wlan.c 与 rfkill-bt.c 仍读取这些原厂属性。BCMDHD 基础配置的固件目录是 /lib/firmware/ap6275p；其 dhd_config.c 还会按芯片重写文件名，所以旧 /vendor/etc/firmware 文件必须按实际逻辑整理后再安装，不能仅凭配置中的 fw_bcmdhd.bin 就认定路径已适配。固件/NVRAM/CLM 与蓝牙 HCD 原件及哈希已有历史归档，暂未装进新桌面根目录；旧 5.10 模块不得复制进新系统。

验证：tools/validate-armbian-peripheral-dt.py 集成编译与 299 项原厂参数比对通过，unexpected_warnings 为空，另核对 GPIO 控制器、PCIe PHY、RTC 时钟/中断及电源 pinctrl 引用。跨 DTB 不比较裸 phandle。新报告标记 wireless_gpio_phy_clock_references_verified 和 wireless_rtc_pcie_uart_disabled。

尚需补齐：UART 引脚/流控及 DMA 运行检查、供电/复位时序、固件/CLM 文件名与可信哈希、蓝牙 helper 在 Debian ARM64 的运行依赖、rfkill 与 NetworkManager、连接/吞吐、配对及休眠唤醒。候选服务不自动启用。

补充：tools/prepare-f8-wireless-assets.py 已将原厂固件5文件和helper按历史归档 SHA256 校验后整理到 /var/tmp/f8-pro-armbian/wireless-assets；报告 analysis/armbian/wireless/verified-assets.json。为驱动默认名称及 ap6275p 小写模块名准备相对软链接，保留原始 NVRAM 内容。目标驱动还可能根据 PCI 子设备编号覆盖模块名，文件路径映射仍需在本机新内核日志核验。helper ELF 为 AArch64/glibc解释器，目前没有执行UART初始化。资产未合入桌面根目录或真机。
