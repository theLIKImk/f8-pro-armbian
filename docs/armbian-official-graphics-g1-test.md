# 官方 Armbian + Panthor + F8 内屏：G1 真机短测

**实测更新：G1已发生GPU电源域上电panic，不再重刷原候选。官方内核和用户态已启动，失败证据及G2修正见[后续说明](armbian-official-g1-failure-and-g2.md)。下文为保留的测试前说明。**

2026-10-29。此轮使用官方 Armbian26.8.1 Ubuntu26.04 KDE根、官方6.1.115-vendor-rk35xx Image及原配模块/固件/Mesa；F8板级配置继续保留已实测的存储、I2C0 m2、UART2和内存信息，GPU子树按本次官方DT重接，不再使用旧Arch libMali或自建Debian根。

## 已准备与核验

- 新根：2148360192字节，SHA256 a6a76aef7feae1d1eb89c615ccbede837d7b4fc657c790580273ef5a20a6f5eb。
- 已确认原Arch/5.10.160 SSH恢复，根镜像新增到/var/lib/f8-pro/armbian-official-26.8.1/rootfs.squashfs；94.5秒完成上传、fsync、独占发布及落盘后重读SHA。未改boot/分区/原配置，无重启。
- 实际GPU目标是Panthor DRM；旧Mali节点disabled，Panthor节点okay，初测只有官方200MHz OPP可用，使用官方电压值。保留原面板1200×1920/160MHz完整时序，启用VOP/IOMMU→VP2→DSI0→面板/供电/PWM14，初始背光32/255。
- 官方桌面extraargs的cma=256M已带入候选，不继续沿用纯诊断的8MiB默认CMA预算。29项显示驱动关键绑定与镜像原配6.1.115 DT一致、没有新增DTC告警；不代表所有外设都已验收。
- 完整5单元依赖、实际KWin命令选项、ARM64 shell/blkid、打包BusyBox modprobe -D依赖读取及模块逐字节配套检查通过。没有真正加载模块或运行GPU。
- 新GPU探针使用GBM render node + surfaceless GLES3 RGBA8 FBO，避免假定Mesa GBM支持pbuffer。读取16×16缓冲的实际像素；必须Panthor、G610、像素正确、没有软件renderer/libMali才记hardware_accepted。实际打包探针在无GPU的ARM64隔离根中会拒绝通过。
- 试验探针/报告/Wayland启动脚本由initramfs复制到RAM upper以更新测试工具；冻结SquashFS和官方GPU库/模块/固件不改。探针与脚本哈希写入boot-manifest，防止实际运行版本不清。

## 这次唯一应选择的 boot

outputs/armbian/official-f8-graphics-r1b/boot-g1b/BOOT_ONLY_ARMBIAN_26.8.1_GPU_G1_CANDIDATE.img

49427344字节，SHA256 **0eddfc105ff790687bc96a84cb580ffb1ca2ba6ee7823fa121beec2510943926**。

父目录及boot-g1a保留封装审查过程，不作为本轮用户测试入口。不要刷downloads中的Orange Pi整盘镜像或把2.15GB SquashFS写到boot。

## 刷入与观察

1. 按已经用过的RKDevTool方法进入Loader，在下载镜像页只勾boot，起始地址0x00008000、分区大小0x00020000扇区，选择上面的G1候选。不要擦除或操作其他分区。
2. 启动并保持USB连接。留意屏幕：可能先出现内核文字；GPU像素读回通过后，才尝试约25秒KWin Wayland会话，显示标题“F8-PRO Armbian Wayland”的测试窗口。没有完整Plasma桌面/登录界面，触摸此轮仍未启用，不需要点按钮。
3. 等待约3–4分钟，Windows应出现卷标 **F8AG1** 的只读日志盘。出现后告诉助手盘符，以及屏幕是否亮、是否出现测试窗口；没有画面也先保全日志。
4. 图形试验有独立超时。报告timer约110秒触发，导出静态RAM快照：GPU.JSON、GRAPHICS.TXT、WAYLAND.TXT、GFXSTATE.TXT、DRM.TXT、ARMBIAN.TXT、MEMINFO.TXT及既有内核/挂载/journal日志。设备日期可能来自内置epoch，不能当真实测试时间。
5. 若4分钟仍无日志盘，可按原方法只刷原BOOT恢复，再收集pstore/日志判断早期失败；没有USB盘不能直接断言内核未启动。

## 验收边界与回退

GPU.JSON的hardware_accepted=true及像素/renderer字段用于GPU验收；KWin日志需要独立确认实际后端和renderer，实物画面由用户确认。只有窗口或启动日志不能算整条图形链通过。首测限200MHz，没有性能、DVFS、休眠或长期稳定性结论。

原Arch分区以PARTUUID核对后ro,noload挂载，仅充当镜像容器；实际PID1、GPU库和Wayland程序来自官方Armbian根，写入留在RAM。没有网络SSH、SDDM或全功能桌面。本轮充电/BQ/CW、触摸等仍禁用。

日志保存后可立即只刷回 outputs/armbian/firstboot-diagnostic/CURRENT-BOOT-ROLLBACK-64MiB.img 恢复使用/充电。原备份67108864字节，SHA256 7e51e71f7ec7439357e5ea2fbb97118715fe5fcf10401b638609df33567b1dd1，已再次核验。

截至本记录：候选预检通过、根已暂存，没有自动刷入、重启或硬件GPU成功记录。说明以boot-g1b/preflight.json及官方基线审计报告为准。
