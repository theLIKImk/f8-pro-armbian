# F8-PRO 转向 Armbian

> 2026-10-29 用户再次明确：直接从官方 Armbian 镜像移植，停止以自行 debootstrap 的 Debian 评估根作为交付基线。已选择官网26.8.1 RK3588S KDE/vendor镜像，具体来源、GPU对比与执行状态见 [正式Armbian基线](armbian-official-baseline.md)。下文包含早期方案，遇到冲突以上述新决定和最新checkpoint为准。

> 最新需求：仅使用 KDE Plasma Wayland；原生 X11 双会话要求已取消。相关旧版本约束与X11验收步骤不再执行。


决策日期：2026-10-28（Asia/Hong_Kong）。用户已决定以 Armbian 替代 Arch Linux ARM 作为后续移植主线。本文优先于历史 Arch 构建步骤；当前工作目录继续保留 archlinux 名称，避免破坏脚本绝对路径。

## 已核对的起点

- 硬件实测为 RK3588S TABLET V11，compatible 为 rockchip,rk3588s-tablet-f12-v11 / rockchip,rk3588；GPU Mali-G610，DSI 1200×1920。
- 当前已知可启动系统为 Arch 用户空间加原厂 5.10.160 内核/设备树。正常启动、Wi-Fi MAC 修复、密钥 SSH、原根文件系统扩容和竖屏五指触摸已有历史验收。
- 本地 TODO/HANDOFF 落后于历史聊天最后一步。聊天“读取并同步 F8-PRO 移植资料”（01a17cd9-3d7e-7482-ae82-cee0e2f34869）记录：KWin 3.4 日志通过（KWin/Qt Mali-G610 GLES、缓冲导入、帧提交、截图和服务退出）；用户随后明确回复“正常，记录一下”。因此旧栈的限时 KWin 测试画面已获确认。该结论来自历史聊天，本轮未复测，不能扩大为完整 KDE、SDDM、虚拟键盘或长期稳定性通过。
- 旧方案依赖私有 GBM/EGL 桥、平台主题修正和 mali_buffer_sharing 兼容原型。迁移目的是评估标准 DRM/Mesa 路径并降低维护成本，不再继续扩大旧驱动兼容补丁主线。

## 迁移分工

用户进一步确认：选择 Armbian 是为了复用其较成熟的 RK3588/GPU 适配，项目自行处理其他硬件。后续优先复用其现成驱动栈，主要投入板级设备树、缺失驱动、固件和服务集成；GPU 与 F8-PRO 内屏的联合测试仍作为验收关口。

## 技术路线与边界

Armbian 提供构建框架和 Debian/Ubuntu 用户空间；更换发行版本身不会替换原厂 kbase，也不会自动解决 GPU ABI 或平板显示支持。

优先评估 Armbian Rockchip vendor 内核分支中的 Panthor 支持，与 Mesa Panfrost 用户空间配套。主线内核作为后续候选。vendor 这个分支名不能证明某个构建含 Panthor，必须检查锁定源码、补丁、配置、设备树和固件，再决定版本。保留原厂 5.10 作为恢复基线，不把旧内核加新 rootfs 认定为 GPU 迁移完成。

Panfrost 是 Mesa 用户空间驱动名称；G610 的目标内核接口为 Panthor DRM。不得在同一 GPU 节点同时启用 kbase 与 Panthor，不只改 compatible，不全局混装原厂 libMali 与 Mesa。GPU 运算成功也不能证明 VOP2/DSI 扫描输出成功，须单独验证 DMA-BUF modifier、显示链和真实画面。

本轮尚未建立 F8-PRO 的 Armbian 板级配置，也未确认官方有可直接用于本机的镜像。其他 RK3588 开发板只可参考 SoC 公共实现，不能将其 DTB、整盘镜像或 U-Boot 直接刷入平板。

发行版先比较官方稳定 Debian/Ubuntu ARM64 软件源的 KDE、Qt、Mesa 和内核配套能力，再锁定一个 release。继续保留原生 Wayland 优先、原生 X11 后续兼容的既有要求；XWayland 不计为原生 X11。Arch 的 Plasma 6.7.5 是旧环境的版本选择，不自动成为 Armbian 的锁定版本；若候选仓库无法提供双会话，应记录缺口并评估一致版本的维护成本，不能静默取消要求。

## 可复用资料与必须重做的适配

| 项目 | 继承资料 | Armbian 要求 |
| --- | --- | --- |
| 启动/恢复 | vendor/ubuntu-5.10.160、现有正常 boot 和恢复说明 | 先检查原 loader/U-Boot 对新内核、FIT、DTB、initramfs 的支持；初期保留 loader/GPT |
| 设备树 | 原厂 DTS/DTB、boards/f8-pro-live-baseline.json | 逐项迁移节点与 binding，不能把 5.10 DTB 直接当作新内核适配成果 |
| 显示/触摸 | DSI 面板时序、供电、背光、gslX680_r8 和触摸验收 | 核对新内核驱动与 GPIO/复位/供电，重测多点及旋转后坐标 |
| GPU | arch-gpu 实验与协议记录 | 使用独立测试根，检查 Panthor/固件/Mesa/DRM 与显示导入，不自动继承旧私有桥 |
| Wi-Fi/蓝牙 | AP6275P 固件/NVRAM/CLM、BCM4362A2.hcd、ttyS9、MAC preserve 修复 | 固件可核对复用；5.10 的 bcmdhd_pcie.ko 不能用于新内核，须重编或验证替代驱动 |
| 声音/摄像头 | ES8388/ES8323、GC5035/OV8858、ISP 与厂商初始化资料 | 新内核重新适配并实测；不能把原厂 rkaiq/模块直接视为兼容 |
| 传感器/电源 | MPU6500、AK8963、CW2015、BQ25890 | 评估 input→IIO 接口、旋转服务、电池/充电、温控、休眠唤醒 |
| 包与服务 | packaging、rootfs-overlay 和 tools 的原始记录 | Arch PKGBUILD/pacman 事务不适用于 Armbian；模块路径、包名、服务及首启流程逐项改写 |

## 执行顺序与验收门槛

1. 保存迁移前现场：确认设备在线后只读检查当前内核、DT、挂载、PARTUUID、GPU 绑定、温度、已安装 KWin 和遗留编译进程；先归档日志，不盲目续编或终止历史 PID。备份当前 boot/配置/用户数据及恢复所需内容，记录哈希。已有 pre-root-grow 配置备份不是当前整盘或完整根快照。
2. 固定 Armbian build commit，核查 Rockchip family 的实际 kernel source/ref、Panthor 补丁/config/固件及 rootfs 包版本。列出 F8-PRO 专属驱动差异；选择主机支持的构建环境。此步完成前不发布可刷写板级配置或冒充可用的 compile 命令。
3. 在独立目录准备最小 Armbian 测试根和 F8-PRO 内核/DT。先串口/USB 日志、eMMC 只读识别、供电/温控、网络/SSH，再测 DSI、背光和触摸。启动方案需要适配现有 FIT 交接机制，不假定 Armbian 默认 extlinux/boot.scr 已被原 loader 支持。
4. GPU 验收：记录实际绑定 Panthor、固件版本、Mesa 库加载、render node 和 renderer；EGL/GBM 离屏像素读回→限时 DRM/Wayland→Qt/KWin 实际帧和实物画面。排除 llvmpipe/softpipe，保留错误日志。无私有 Mali 协议桥的标准客户端路径应独立通过。
5. 安装一致版本 KDE/SDDM，验证原生 Wayland 和后续原生 X11，分别记录 compositor/client renderer、稳定性与恢复。验证登录界面和桌面输入框触摸自动弹键盘、实际输入、收起、锁屏及旋转。
6. 重做音频、摄像头、传感器、无线重连、蓝牙、充电、休眠/唤醒和接口全项验收；原内核下通过的项目不能直接记作新内核通过。
7. 移植首次账户向导：保留原需求的临时 alarm 向导身份，按目标发行版实现；新管理员登录、sudo、网络、桌面及键盘验证成功后再移除测试账号与诊断权限。交付中不得保留私人网络、测试密钥或依赖 alarm 家目录的组件。

以上均为待执行任务；本轮完成的是资料核对、迁移决策和计划更新，未生成/安装 Armbian 镜像，未更换运行中的 GPU 驱动。

## 存储与恢复约束

历史根分区为 /dev/mmcblk0p6，起始 LBA 0x78000（491520），PARTUUID 614e0000-0000-4b53-8000-1d28000054a9；boot 起始为 0x8000。这里只作对照，执行前必须重新读回确认。已有误将 rootfs 写到 boot 起点导致跨分区覆盖的记录，严禁复用未核对的刷写行或向 eMMC 写入其他板整盘镜像。

初期保留现有 Arch 根、正常 boot、原厂恢复资产和机器身份；独立介质或独立测试根的具体位置须按实机启动支持及空间确认后选择。不改现有分区边界，不清理旧源码与产物，不移动整个项目目录。

## 构建环境与后续审计

2026-10-28 在当前环境执行 wsl -l -q 返回 Wsl/EnumerateDistros/Service/E_ACCESSDENIED。因原 SSH 工具依赖 WSL 的专用密钥与 known_hosts，本轮未通过该通道访问平板，也未核验旧编译是否结束。此限制与平板故障无关。后续先恢复构建环境访问，再做执行顺序第 1 步。

## 官方研究来源（2026-10-28 查询）

- [Armbian 板级配置](https://docs.armbian.com/build-framework/board-configuration/)：需要专属板配置、family、DT 和启动设置。
- [Armbian 构建命令](https://docs.armbian.com/build-framework/commands/basic/)：可分别构建 image/kernel/U-Boot；待板级配置确认后再形成可执行命令。
- [Rockchip RK3588 family 源码](https://github.com/armbian/build/blob/main/config/sources/families/rockchip-rk3588.conf)：当前 vendor 路线调用公共 vendor 配置；main 为动态引用，本轮未将它锁定为构建输入。
- [Mesa Panfrost 文档](https://docs.mesa3d.org/drivers/panfrost.html)：支持 G610；GPU 与显示控制器需分别适配。上游支持不等于本平板验收。

后续更新：提权后已恢复 WSL 与 SSH，现场健康检查通过；先前访问限制已解除。固定源码与硬件差异见 [首轮硬件审计](armbian-hardware-audit.md)。

最新外设适配与编译证据见 [外设草稿核验](armbian-peripheral-draft.md)。
