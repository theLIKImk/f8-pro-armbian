# 蓝牙 BT1 测试（2026-11-01）

**最新验收覆盖下方“待刷/尚未冷启动”：用户已刷入并确认“启动后正常，蓝牙工作正常，能够扫描设备”。SSH 实测新 boot `5da89e9f-10f3-4d00-87bf-97df844b1100`，ttyS9、RTC 和蓝牙平台绑定正常；HCI 控制器 Powered=yes，32k 时钟 32768Hz、enable/prepare=2/2；f8-bluetooth 开机约10.5秒启动、NRestarts=0、enabled，BlueZ/USB OTG/SDDM active、系统0failed。此次仅取证，没有重新扫描或主动配对。证据 `local/hardware/bluetooth-bt1/after-boot01.json`、`verification01.json`、`user-feedback01.json`。控制器及开机自动加载、用户扫描通过；配对、实际蓝牙音频和休眠恢复尚未获得用户验收。BT1作为后续BOOT基线，U5保留回退。**

## 当前定位

U5 实机 boot `a56f9a1a-ca82-4f4d-96d3-fbf4df432102`：BlueZ 5.85 正常运行，但没有 HCI、蓝牙 rfkill 或 ttyS9。蓝牙平台、UART9、HYM8563 RTC 时钟节点均 disabled，不是单纯 KDE 开关问题。UART9 是 `/serial@febc0000`（不要与 UART6 feb90000 混淆）。

板级资料、原厂运行命令与现有 DT 对照：AP6275P 的蓝牙使用 BCM4362A2.hcd、UART9 m2、1.5M 波特率；TX/RX GPIO3_D4/D5，CTS GPIO3_D3，RTS GPIO3_D2；reset GPIO0_D4、wake GPIO0_C6、host-wake GPIO0_C5；HYM8563 I2C6 0x51 提供 32768Hz。已核对本地匹配 vendor 源码的 rfkill GPIO/时钟读取方式与 RTC 时钟提供逻辑。当前对应引脚无占用记录。没有运行 I2C 扫描、手动 GPIO 操作或更改 Wi-Fi。

## 已完成

- BOOT 从已验证 U5 提取，仅启用 UART9、蓝牙平台、RTC，显式请求 RTC 32768Hz，增加 chosen `f8-bluetooth-trial=bt1`。
- 保留完整 CPU cmdline 黑名单、USB U5 profile、原 kernel/ramdisk、音频/背光/触摸配置。FIT 与 resource 内 DT 同步，原 logos 保留；逐属性限定差异、FIT 哈希、内存边界、64MiB 容量检查通过。
- root 已安装并 enable `f8-bluetooth.service`，未 start。没有 ttyS9 或试验标记时条件跳过，U5 回退不会等待串口、不会初始化蓝牙。
- helper 与原厂 HCD 均核对历史可信 SHA256；ARM64 loader 依赖检查通过。不复制旧内核模块。
- 服务在桌面和 USB 服务之后独立启动，使用现有 hci_uart，稳定本地 MAC 延续旧 machine-id 派生方法；失败最多按服务限制重试，不依赖蓝牙才能启动桌面。

固件：`/usr/lib/firmware/f8-pro/BCM4362A2.hcd`，SHA256 `18901a5bef1d418b6895e92d0afae36234f4160b237465dfca3d75e9844e93ef`。
helper：`/usr/libexec/f8-pro/brcm_patchram_plus1`，SHA256 `f69ba38d29d7745e88df7cfec6314a1704929dfbaf029fdd8f9c4f140e907d03`。
项目服务与启动器在 `armbian/bluetooth/`。完整安装哈希证据 `local/hardware/bluetooth-bt1/install01.json`；改前状态 `local/hardware/bluetooth-before-20261101.json`。本镜像本身不安装 root 服务文件，后续新 root 打包必须加入 runtime-integration.json 所列资产。

## 待用户刷入

文件：`outputs/armbian/official-f8-bluetooth-bt1/BOOT_ONLY_ARMBIAN_BLUETOOTH_BT1.img`。

- 49445912 字节。
- SHA256 `de2d364e8163914e7996332d1551c07bf9e50316c6b1bf0f3d22dfd61dab6cb1`。
- RKDevTool 仅勾 boot，地址 `0x00008000`；不刷 rootfs、Loader 或整盘，不擦除。
- 先安全移除外设，拔下 U 盘，再进 Loader 刷 BOOT；启动联网后回复状态/IP。
- 回退使用 `outputs/armbian/official-f8-native-usb-u5/BOOT_ONLY_ARMBIAN_NATIVE_USB_U5.img`，仍只刷 boot。

尚未冷启动、控制器初始化、扫描、配对、蓝牙音频或休眠验收。启动后先用 `tools/read-f8-bluetooth.sh` 通过固定主机公钥 SSH 保存新快照，核对新 boot ID、ttyS9、rfkill、RTC clock、服务日志和 HCI，再进行有限时长扫描及用户指定外设配对。继续不改 BQ25890 充电策略或 PD 参数。
