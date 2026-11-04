# 从正式 Armbian 镜像移植 F8-PRO（2026-10-29）

2026-10-29后续：F8官方Armbian GPU/内屏候选及新根暂存已完成，尚未真机测试，见[本轮测试说明](armbian-official-graphics-g1-test.md)。以下基线审计保留。

用户明确要求直接从 Armbian 开始，复用其 RK3588/GPU 集成。本决定取代此前“自行 debootstrap Debian Trixie + 仅取 Armbian 内核源码”的交付主线。R1–R5保存为启动、供电总线、SMP、只读存储和RAM用户态诊断证据，不扩大为正式Armbian或GPU验收，不再增加同类纯基础启动刷机轮次。

## 已选基线

官方 Armbian 26.8.1，Orange Pi 5 / RK3588S，Ubuntu 26.04 Resolute，KDE Plasma desktop，vendor 6.1.115。

文件：Armbian_26.8.1_Orangepi5_resolute_vendor_6.1.115_kde-plasma_desktop.img.xz。

官方公布SHA256：fae6bd998cf8bf75274a367f1f3937aae609d6560e3110df35434cf6a9a45612。

压缩大小1576708364字节。它是移植输入，不是F8-PRO整盘刷机文件。只在电脑解包/只读审计；原loader/GPT/Arch恢复资产保留。使用Orange Pi 5是因为同为RK3588S，板级电源/屏幕/存储启动配置仍按F8重新适配。

来源为[官方Orange Pi 5镜像页](https://armbian.com/boards/orangepi5)，其列出vendor6.1.115和current6.18.43两种KDE镜像。优先vendor以保留原厂BSP外设接口，不能据此声称GPU性能超过current；current作为后续参照。官方页面对推荐镜像的稳定声明针对Orange Pi 5，不代表本平板已获支持。

## 对比与必须确认的内容

| 项目 | 原Arch/5.10方案 | R4/R5临时评估 | 正式Armbian新主线 |
| --- | --- | --- | --- |
| 系统来源 | Arch根与原厂内核 | 自建Debian Trixie根、自编6.1.172 | 官方KDE镜像，保留软件包来源与BSP记录 |
| GPU | 旧kbase/libMali及私有GBM/EGL桥 | Panthor模块已构建，但GPU节点禁用，未测 | 复用官方Panthor/Mesa集成，审计实际节点/overlay及库 |
| 模块ABI | 5.10.160 | 6.1.172-f8-pro-armbian-eval | 以所选镜像实际6.1.115 release与符号表为准 |
| 桌面 | 旧栈有历史限时KWin测试 | 本轮未启动桌面 | 保留官方KDE，配置Wayland/SDDM和触摸键盘 |
| 板级差异 | 原厂DT已知 | 部分F8节点完成迁移 | 迁入F8供电、内屏、触摸、无线等；不套用OPi板参数 |

开源路线的优势是标准DRM、Mesa和发行版维护路径；尚无同机GPU性能或稳定性对照，不能写“已实证更快”。[Mesa官方文档](https://docs.mesa3d.org/drivers/panfrost.html)列出G610支持，且指出Mali是3D GPU，显示控制器需单独集成，所以渲染通过仍需验证VOP/DSI扫描输出。GPU固件可能仍是二进制，不把开源驱动等同于所有组件都开源。

固定Armbian build审计commit仍为98692adee6442f6f221200cf8e6642f9c6a7b740；这是参考构建框架快照，不能冒称本次26.8.1镜像的真实构建commit。真实信息从镜像/etc/armbian-release与包数据库读取。GitHub os/latest返回trunk版本，已放弃用它代替官网稳定镜像目录。

## 接下来的执行门槛

1. 完成下载、官方SHA比对与PGP验证；签名key指纹按[官方验证文档](https://docs.armbian.com/getting-started/choosing-an-image/)核对。工具记录每一步，不把只下载签名当验签通过。
2. 原始镜像在WSL以ro,noload挂载，提取armbian-release、包清单、内核config、模块release、Panthor固件/overlay和Mesa/KWin/SDDM版本，不运行镜像服务或维护脚本。
3. 在独立可写移植根中保留官方GPU库/固件/模块配套。明确旧kbase节点关闭、Panthor节点启用；不能混入旧Arch libMali或6.1.172 ko。需要自编时通过Armbian框架接入F8配置，明确版本与差异。
4. 复用已证实的F8启动交接、I2C0 m2、UART2与只读保护，将DSI/背光/触摸等适配到此基线。先确认官方内核对F8设备树绑定；不把旧6.1.172 DT的编译结果当6.1.115验证。
5. 下一次真机候选应覆盖开源GPU实际绑定、render node、固件加载、Mesa renderer与像素读回，随后内屏Wayland/KWin实际画面；禁止以llvmpipe或私有桥通过替代。

审计资料在analysis/armbian/official-gpu-baseline-20261029/，下载在downloads/armbian/official-desktop-26.8.1/。不将该下载镜像加入F8刷机清单；新候选尚未准备好时继续保留原BOOT回退方式。

## 官方镜像实读结果与已准备目录

SHA256和PGP签名均已通过；原始镜像解压为8438939648字节，GPT CRC检查通过。只读挂载并完成检查后已卸载，没有运行其中的服务或维护脚本。

镜像实际/etc/armbian-release为stable26.8.1，BOARD=orangepi5、LINUXFAMILY=rk35xx，记录的构建commit短值为8b778f3d8。它与先前固定的参考build快照不是同一来源标识，必须分别记录。

实际软件：Mesa26.0.3-1ubuntu1、KWin/Plasma6.6.5、SDDM0.21.0+git20250502.4fe234b-2ubuntu3、armbian-firmware26.8.1；包含G610所需arm/mali/arch10.8/mali_csffw.bin和panthor.ko。没有发现libMali库；Mesa的mali-dp_dri.so和相机IPA不是libMali。

**默认DT启用旧Mali、禁用Panthor，boot/armbianEnv.txt没有启用Panthor overlay。** 因此不能声称“换成这个Armbian镜像就自动用了开源GPU”。官方附带rockchip-rk3588-panthor-gpu.dtbo，其关闭gpu、启用gpu_panthor并引用vdd_gpu_s0。离线fdtoverlay实测这三项通过；供电符号实际解析到/spi@feb20000/rk806single@0/regulators/DCDC_REG1。该结果针对官方参考DT，尚未当作F8-PRO DT验收。

已用cp -a复制完整官方根到WSL独立目录：

`/var/tmp/f8-pro-armbian/f8-official-armbian-26.8.1/rootfs`

保留Linux所有者、权限与符号链接；它与冻结Trixie根无共享hardlink，不修改原始官方镜像。根目录尚未应用F8板级修改、尚未启动。

精确配套资产：

| 资产 | SHA256 |
| --- | --- |
| 官方26.8.1 Image，46561792字节 | a67daf71caefef6b97a22ba708bbb302b239a4a9b4874cadd17a217ebd0c37b7 |
| panthor.ko，249728字节 | dde1617d0fb8c39fb04cb471d0eae28aab5afdbd71771605947d3c912604107f |
| G610固件，282624字节 | a27847ea11f8efb3136340c3ba8aab413ae25145eeb4a7f64ff5edd829a2405b |

旧26.8.3包的Image哈希是28369957…80d108，与本次不同，尽管uname release同为6.1.115-vendor-rk35xx。旧26.8.3 headers/符号表和额外电池模块不能直接视为本镜像匹配；需要逐符号/配套来源重新核验。6.1.172的模块更不能混用。

结果文件：downloaded-desktop.json、official-image-inspection.json、prepared-official-root.json及signature-verification.log。下一步对接F8设备树/现有FIT loader，并明确启用Panthor；本轮没有新F8 boot候选或真机GPU测试。
