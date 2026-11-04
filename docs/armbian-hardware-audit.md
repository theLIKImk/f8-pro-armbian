# Armbian 首轮硬件适配审计

> 最新需求：仅使用 KDE Plasma Wayland；原生 X11 双会话要求已取消。相关旧版本约束与X11验收步骤不再执行。


日期：2026-10-28。源码存在、配置启用和真机功能通过分别记录，不能相互替代。

## 当前现场

已通过提权后的现有 WSL/SSH 通道只读访问平板，先前 E_ACCESSDENIED 是沙箱访问限制。systemd 为 running，失败单元为空；未发现 kwin_wayland、weston、makepkg、cc1plus 进程或残留 f8-wayland 测试单元。当前 VT 为 tty1。根分区 /dev/mmcblk0p6：227G，总使用约 5.6G、可用约 221G。KWin 日志末尾确认 6.7.5-3.4 打包完成。本轮未安装软件、改驱动、刷写或重启。

## 已固定的审计输入

- Armbian build：98692adee6442f6f221200cf8e6642f9c6a7b740。
- Armbian linux-rockchip：85233a85b67928000afc2e966bab86a8c414f1b4（rk-6.1-rkr7.2）。
- 构建框架 vendor 选择 6.1，vendor-next 选择 6.12；本轮先审计 vendor 6.1，以尽量保留原厂 BSP 硬件接口。
- 输入文件及 SHA-256：analysis/armbian/source-audit/manifest.json。此为源码审计快照，尚未锁定完整构建工具链、全部补丁、固件和软件源，不能称可重现镜像已准备完成。
- 原厂反编译 DT 的 36 个相关节点、453 个 phandle 路径映射：analysis/armbian/board-evidence.json。每个节点保留原行号与完整文本。数值 phandle 仅对原 DT 有效，移植时必须恢复符号引用。

## 首轮差异

| 硬件 | 原厂资料 | 候选 6.1 已检查结果 | 下一步 |
| --- | --- | --- | --- |
| GPU | Mali-G610，旧 kbase | Panthor Kconfig 存在，框架配置 CONFIG_DRM_PANTHOR=m | 核对 GPU DT、固件和 kbase 互斥，再做与内屏联合测试 |
| DSI 屏幕 | dsi0/panel@0，simple-panel-dsi，4 lanes，1200×1920，160MHz | panel-simple.c 保留 simple-panel-dsi 匹配和可选初始化序列解析 | 复用原面板时序、供电、复位和 graph 连接；原节点没有 panel-init-sequence，不编造面板命令 |
| 触摸 | i2c4，0x40，gslX680_shuping；screen_max 1200×1920 | CONFIG_TOUCHSCREEN_GSLX680_PAD=m，gslx680_pad.c 存在 | 驱动名称相似不等于匹配；继续核对 OF、固件表、坐标和引脚。不能仅改 compatible 强行绑定 |
| 音频 | i2c7 0x11，everest,es8388 / everest,es8323；multicodecs 声卡 | es8323.c 匹配 everest,es8323，配置 ES8323 与 MULTICODECS 已启用 | 原 DT 第二 compatible 有候选匹配；核对 I2S/MCLK、功放 GPIO 和声卡 routing，再实测录放音 |
| 摄像头 | i2c5，GC5035 0x37 前摄、OV8858 0x36 后摄 | 两驱动源码存在，两个 VIDEO 配置为 m | 迁移电源/复位/时钟和 CSI graph；另查 ISP、IQ 文件与相机应用，节点存在不算拍照通过 |
| 加速度/陀螺仪 | i2c3，同一 0x68 的原厂 acc/gyro 子设备 | 两个厂商 sensor 驱动源码存在，配置均为 m | 优先核对原 sensor 框架及共享芯片机制；不可直接换成两个独立 IIO 客户端抢同一地址 |
| 罗盘 | i2c3 0x0f，ak8963 | 厂商 compass/ak8963.c 存在，CONFIG_COMPASS_AK8963=m | 核对公共 sensor 匹配、方向矩阵和服务接口；不因 IIO 路径 404 误判缺驱动 |
| 电量计 | i2c6 0x62，cellwise,cw2015 | cw2015_battery.c/Kconfig 存在；当前框架配置未列 BATTERY_CW2015，列有不同型号 CW2017 | 为本机明确启用 CW2015；按 64 字节配置解析保留原 battery profile，不更换为其他电池曲线 |
| 充电 | i2c6 0x6a，ti,bq25890 | bq25890_charger.c/Kconfig 存在；框架配置未列 CHARGER_BQ25890 | 明确启用后逐项比对属性解析，保留本机电流/电压约束，不直接照搬其他板参数 |
| Wi-Fi | AP6275P、bcmdhd_pcie，固件/NVRAM/CLM 已归档 | 框架配置 BCMDHD_PCIE=y，但默认固件路径为 /lib/firmware/ap6275p | 核对 PCIe/供电/复位；按本机固件组织目标路径，继续保留 MAC preserve 修复 |
| 蓝牙 | ttyS9、BCM4362A2.hcd | 尚未检查目标 UART/蓝牙匹配 | 迁移串口、供电、唤醒 GPIO 和初始化服务，再测试配对/音频/休眠恢复 |

CW2015、BQ25890 所需配置记录在 armbian/kernel/f8-pro-vendor-6.1.fragment。该文件只是待合并片段，尚未接入构建框架或通过 olddefconfig/编译，不表示实际内核配置已改变。

## 下一阶段

先核实触摸固件/匹配及厂商 sensor 框架，再以同一锁定内核的 RK3588S SoC include 构造本机符号化 DTS。DSI、eMMC、供电、温控、网络是首启前置；电池与充电配置不能遗漏。完成 DTS 编译、配置依赖检查与恢复资产备份后，才准备独立测试启动产物。

本轮未直接生成板级 .conf：BOOTCONFIG、BOOT_FDT_FILE 与原 FIT 启动方式尚未完成验证，填入其他开发板值会产生误导。

源码依据：[Armbian build 固定提交](https://github.com/armbian/build/tree/98692adee6442f6f221200cf8e6642f9c6a7b740)、[linux-rockchip 固定提交](https://github.com/armbian/linux-rockchip/tree/85233a85b67928000afc2e966bab86a8c414f1b4)。具体文件链接与哈希见本地 manifest。

后续进展：触摸主比较对象已由真机配置确定为 GSL3673，而非 PAD；固件对比、外设草稿编译和单/双 RK806 差异详见 [外设草稿核验](armbian-peripheral-draft.md)。
