# F8-PRO Armbian 接续（2026-10-29）

目标仍为 KDE Plasma Wayland + SDDM、登录与桌面自动虚拟键盘及全部实际硬件适配。此文优先于 2026-10-28 的后台进程信息。

## 第三十九轮（2026-10-30）：r4正式系统启动，r5修目标安装并移除弹窗

r4用户见旧测试弹窗和Network connection timeout；49日志归档。正式systemd启动通过，无线固件/NVRAM/CLM下载及wlan0注册、GPU硬件检查通过，但新live服务均无日志、无IP/22监听。发现真实init资产case漏*.target，新增目标错放usr/libexec，旧目标继续运行。r5补目标安装分支，并实际执行最终CPIO内安装循环到隔离目录，再用实际安装结果验证服务图；不是手工代装到正确路径。取消自动KWin弹窗，只初始化驱动和无界面GPU检查，保留状态页/SSH/持续只读电源。

新唯一outputs/armbian/official-f8-live-g6-r5/BOOT_ONLY_ARMBIAN_26.8.1_LIVE_G6_CANDIDATE.img，50077396字节SHA3768f600bb84e1be2cd18b3895e0e762effbf365600969e258074ca5288265c9，F8AG6。离线检查通过，真机状态页/SSH待测。当前最后r4，先只刷boot确认IP/SSH后再接充电器。最新入口docs/RESUME-NEXT-2026-10-30.md，无后台任务。

## 第三十八轮接续：r3早期Rust工具崩溃，r4拆分固件与正式系统配置

r3的14份init失败日志归档，固件链接已通过，目标Rust coreutils在rustix auxv初始化unwrap失败Aborted。脚本中chroot chown最可疑，但旧日志无阶段标记不能证明具体调用；早期目标root未有/proc。r3预检已标真机失败。

r4撤去init阶段所有目标账户/SSH工具，只保留BusyBox公开固件复制。f8-live-prepare.service在basic.target后配置原Arch私有网络/SSH，仅SSH/联网Require它，图形/状态页/报告独立，因此配置失败仍可启动界面和正式日志。新增SETUP.TXT分阶段标记。实际BusyBox固件覆盖/字节比对，以及/proc/dev/run齐备时真实ARM64账户/原生chown/sshd配置测试通过，setup-fixture-systemd-r4.json已保存；服务图/CPIO/FIT/FAT/shell/布局重新通过。

唯一候选outputs/armbian/official-f8-live-g6-r4/BOOT_ONLY_ARMBIAN_26.8.1_LIVE_G6_CANDIDATE.img，50077616字节，SHA890d976d59f78805ad09e341dff5ffd6322639805cad565c56e62fb1d38b309e，F8AG6。内核/DT/供电策略不改，SSH/状态页待真机。当前最后真机r3init失败，可原BOOT回退；只刷boot后先IP/SSH再接充电器。无后台任务。

## 第三十七轮接续：G6 r2早期FW链接冲突修复为r3

用户反馈无标识、SSH不可用。F:已有早期init-failed日志，14文件归档local/hardware/armbian-official-g6-r2-failure-20261029-01。STEPS为BusyBox cp -a不能创建已有nvram_ap6275p.txt链接，尚未systemd，两个功能均未启动。PCIe Gen1x1建链已证实，未宣称WiFi通信成功。r2预检标实测失败并备份。

live-setup对已知固件各条目仅删除RAM overlay同名入口再cp -a，不递归删除/不改冻结根；前次测试用GNU cp未覆盖此行为，现实际initramfs BusyBox sh及cp/rm/mount/chroot等工具，预置已有链接，setup与sshd配置校验通过。结果setup-fixture-busybox-r3.json。r3重新做服务图/FIT/CPIO/FAT/shell/布局校验，唯一候选outputs/armbian/official-f8-live-g6-r3/BOOT_ONLY_ARMBIAN_26.8.1_LIVE_G6_CANDIDATE.img，50077408字节SHAc39f06385d42c89909de0fe9258931a05f78ad57e79a78b1ef6cfdc3b5486172，F8AG6。DT/内核/供电策略未变，真机SSH/状态页未验收。更新G6指南，先重刷boot取IP再SSH，之后换充电器。无后台任务。

## 第三十六轮接续：G6 WiFi SSH/动态状态页候选预检完成

用户要求SSH启动、随后接充电器远读，若正常作后续测试BOOT，要求TIME/POWER/F8 RK3588S PAD/闪烁BOOT。G6从G5启用原厂无线/PCIe/PHY物理线路，官方bcmdhd和归档固件；原Arch网络及SSH认证材料启动时仅复制RAM。f8test专用公钥登录、测试sudo，关闭密码/root SSH，保留原主机身份，配置显式开放用户会话。tty2动态页显示运行时长/CW电量电压/当前IP和0.5秒闪BOOT；Wayland30秒后返回。10秒持续只读电源，日志timer100秒约2–3分钟，仍无充电策略写入。

隔离overlay虚构凭据的真实ARM64setup/sshd配置验证通过，最终服务图与FIT/CPIO/shell/FAT/布局检查通过。唯一候选outputs/armbian/official-f8-live-g6-r2/BOOT_ONLY_ARMBIAN_26.8.1_LIVE_G6_CANDIDATE.img，50077300字节，SHAfd8a92a56eb5e5576763ea1a3c1c07cb208bf3b4b7786c6a2660bb98a98b1d1d，卷F8AG6。首个offline-g6草稿未发布，不用。见docs/armbian-official-live-g6-test.md，先只刷boot发屏幕IP，确认SSH后再换充电器；无线/SSH/显示/充电待真机，未提升基线。最后真机G5，无后台任务。

## 第三十五轮接续：G5供电只读真机通过，解释210秒日志等待

45日志归档local/hardware/armbian-official-g5-20261029-01。44.187/253.887秒快照均完整，I2C6 m3/BQ/CW通信成功，CW曲线与原厂全同，normal/100%/单读4238→4225mV。BQ PN3，原始寄存器两次全同，设置输入3A/充电2.944A/VREG4.4V/ITERM64mA，CHG开OTG关WD关timer开；实际电流与ADC时效未验证，不是充电通过。注意原系统sysfs2.496A不同于当前2.944A，旧策略仍要核清。GPU通过、触摸存在，无panic快照。

用户问为何盘慢：试验timer210秒加约44秒启动和整理时间，FAT关闭后才导出只读盘，4–5分钟属固定流程。下一版可缩短等待，但不能主机挂载同一FAT时写入。读docs/armbian-official-power-g5-result.md。日志已存可回原BOOT充电，当前G5，下一步有界5V控制/电量接口及IRQ/USB-C适配，G6尚未生成，无后台任务。

## 第三十四轮接续：G5供电只读诊断预检完成

G5从实测G4派生，只修I2C6原厂m3 GPIO4_B0/B1并补RAM日志脚本，BQ/CW保持disabled。读前核验物理bus/引脚/无驱动绑定与地址未占用；通过内置i2c-dev读固定配置，协议写消息严格仅寄存器指针，无配置值写入，无扫描/ADC启动/复位/PD/OTG，跳过BQ0C故障锁存。保留完整原始值与芯片PN校验，CW曲线与原厂对比，早晚各采一次。协议fixture、ARM64无硬件负向探测、shell/FAT/CPIO/FIT四负载及内存布局全部通过，尚未真机读取。

候选outputs/armbian/official-f8-power-g5/BOOT_ONLY_ARMBIAN_26.8.1_POWER_G5_DIAGNOSTIC.img，49473972字节，SHA5426928173b5c79b3a6930416f3b0c86aefdb17acd7824391e20d072809f1697，卷F8AG5。按docs/armbian-official-power-g5-test.md只刷boot，连接电脑等待4–5分钟，不切换到充电器验证。根不用重传。采POWER0.JSON/POWER1.JSON/POWERLOG/POWERBUS，complete只表示读完整；不是充电成功。用户实际回退原BOOT尚未确认，最后实测G4，原系统可正常方式充电。无设备部署或后台任务。

## 第三十三轮接续：G4触摸通过，日志完整归档，供电适配前置审计

用户确认触摸/GPU工作。F8AG4的40文件已保存，触摸2257事件、19按下、最多双指；GPU硬件像素读回通过。G4 preflight加实际通过状态并留备份。供电是下一优先项；充电器铭牌5V3A/9V2.22A/12V1.67A，协议未确认。已核对I2C6原厂m3与候选m0差异、旧BQ限制参数缺失及IRQ/OTG问题，官方I2C_CHARDEV内置且未发现匹配BQ/CW模块。先做定点只读配置诊断再接5V充电，G5尚未生成。用户可先回原BOOT充电，实际回退未确认。详情docs/armbian-official-g4-result-power-next.md。无设备写入或后台任务。

## 第三十二轮接续：G3 I2C超时定位，G4恢复原厂I2C4引脚

G3的37份日志已归档，模块注册成功但控制器probe首次I2C超时-110，input被撤销，TOUCH.JSON零事件。GPU仍为Panthor/Mesa G610硬件读回通过，Wayland启停成功，快照无panic/Oops。原厂I2C4 m3是GPIO1_A2/A3，G3误用m0的GPIO3_A5/A6；失败发生在固件上传前。

G4新增m3组并切换I2C4 pinctrl引用，物理引脚及电气配置与原厂一致，其余DT只改model。完整触摸模块/固件/内核/GPU/根不变，RAM日志补KWin进程/用户及I2C绑定查询，卷F8AG4。FIT全部负载哈希、CPIO受限差异、ARM64 shell语法、FAT、内存布局检查通过。候选49471336字节SHA f55b7e59dc5f8ea029dbf04c438c018339f35166b9907ae3fcb9ed7432ff011b，outputs/armbian/official-f8-touch-g4/BOOT_ONLY_ARMBIAN_26.8.1_TOUCH_G4_CANDIDATE.img。触摸修复尚未真机验证。

下一步见docs/armbian-official-touch-g3-failure-g4.md，只刷boot0x8000，根不重传；尝试90秒窗口触摸，等4–5分钟F8AG4日志。G3日志保存完成可随时回退；充电仍先恢复原BOOT，当前最后确认设备G3。全I2C静态审计另发现I2C3/5/6引脚差异，未随G4修改，留给对应外设核对。无后台任务、无设备刷写。

## 第三十一轮接续：官方ABI触摸模块与G3试验候选就绪

- 用户要求继续。build-f8-official-touch-module.py从原r8/shuping候选派生独立f8-gsl-shuping名称，移除通用OF/platform alias，配置缺失就ENODEV，保留所有已审查传输/PM/输入函数；不改旧候选。算法按官方Makefile私有链接gsl_point_id.c，避免调用未导出内核算法/共享状态。
- 完整模块f8_gsl_shuping.ko为91680字节，SHA bb8fd9db0bf16972e6760ca9d8ba8489e91a516c31269fc770346fe75d7a505d，位于armbian/touch/official-6.1.115-f8。用现有26.8.3 headers构建，但明确不是26.8.1原包；新模块48项导入包括module_layout逐项从实际官方26.8.1模块ELF __versions取CRC比对全一致，有每项参照来源，不绕过vermagic或CRC。完整链接后38808/2048字节板级数组与原厂参考相同。
- check-f8-touch-algorithm-version.py静态解码ARM64版本返回常量，支持目标PAC/函数跟踪序言；新模块与官方stock版本函数字节相同，新/stock/原厂5.10均0x20140421。只能证明版本一致，不冒称全部算法行为等价。原厂probe归档指令0x14864e4设置request_threaded_irq x3=1，核对rising一致。GPIO1_B5 IRQ/B4 reset与原DT不改。
- G3以已测G2真实候选为输入，DT只改i2c4/ts@40 compatible=f8-pro,gslx680-shuping-eval与okay及model，其余完全相同。boot RAM upper安装单独ko到/usr/libexec/f8-pro，由试验脚本手动insmod，不改根modules数据库/不重传2.15GB镜像。实际controller固件上传仅在用户启动G3时发生，当前未加载模块或写控制器。
- 触摸只读event工具不EVIOCGRAB/不读取键盘，严格按f8-gsl-shuping名称发现，记录ABS轴元数据、触摸事件/press-release/多点统计、有限头尾帧约110秒，原始坐标800×1280。GPU严格读回仍先于KWin，窗口延至90秒，可提前点OK关闭；root试验超时190/Wayland110/报告210秒。KWin stdout/stderr显式journal，KWIN头尾和RENDER筛选补采，保留已测GPU配置。
- 最终候选outputs/armbian/official-f8-touch-g3/BOOT_ONLY_ARMBIAN_26.8.1_TOUCH_G3_CANDIDATE.img，49471132字节，SHA256 3797899c1444efde96c1c64e4c4ee618fa4e4f8f67de83a0ae6f4b67d1155b7b，卷F8AG3。新单元参数离线验证、ARM64无触摸明确报错、shell/FAT/cpio/FIT/12KiB布局均通过。根/内核/固件库不改，预检允许用户协调短测，硬件touch仍未验证。

下一步按docs/armbian-official-touch-g3-test.md只刷boot，尝试拖标题栏/点击/多指、等4–5分钟F8AG3后采TOUCH.JSON/TOUCHLOG/INPUT/IRQ/TOUCHDRV/KWIN/RENDER及旧日志。保留G2为图形已测基线，不把窗口90秒自动关闭当失败。充电仍禁用，已告知先回原BOOT充电，最新回退状态未确认。无新设备写入/自动刷机/后台任务。

## 第三十轮接续：G2 Panthor/像素读回/实物窗口通过，转向触摸

- 用户报告弹窗出现后自行关闭、无法触摸，随后报告屏幕似乎能显示终端文字。确认F: F8AG2，30文件保存local/hardware/armbian-official-g2-20261029-01/，summarize-f8-official-g2.py验证并生成test-result.json/文件哈希。无设备写入。G2 preflight加实测结果并留before-hardware副本。
- GPU.JSON hardware_accepted=true，Panthor renderD129，Mesa/Panfrost Mali-G610 MC4、GLES3.1 Mesa26.0.3，software=false，RGBA8像素[64,128,191,255]/GLerror0，无libMali。固件git95a25d71030715381f33105394285e1dcc860a65。G2 GPU域供电修正硬件实证有效；GPU轨仍会先被cleanup关闭，随后PD成功启用，未改电压或panic保护。
- DRM card0/rockchip DSI-1 connected/enabled1200x1920，VP2设置160MHz，card1 Panthor，当前/唯一GPU频率200MHz。logind typewayland会话、用户实物弹窗确认、启动/停止exit0成功；25秒后是脚本主动结束。不是完整Plasma/SDDM或长期稳定性测试。
- KWin stdout跟随tty，WAYLAND.TXT只有systemd/PAM记录，没有独立compositor renderer字符串。下一候选显式StandardOutput=journal、StandardError=journal补采，不把GPU探针renderer冒作KWin查询。42.08秒切换彩色framebuffer console150x120、fb0 rockchipdrmfb，与用户屏幕文字相符；外接UART未测。
- 系统running/0failed，p6ro,norecovery/只读SquashFS/RAM overlay保持，无panic/Oops快照到154.665秒。VOP supply/DVFS fallback、panel bpc0、额外overlay planes、RGA、监管数据库、AppArmor fusermount告警仍在。触摸、充电、DVFS/负载/休眠/完整桌面均未验收。
- 开始触摸匹配审计：audit-f8-official-touch-abi.py输出official-gpu-baseline-20261029/touch-abi/audit.json。官方26.8.1的gsl3673-800x1280/gslx680-pad模块分别50/53项CRC与现有26.8.3 headers全部一致；完整config仅RTL8723DS差异。但尚未验证新F8候选全部导入，不视为可加载新驱动。内核算法gsl_DataInit/alg_id_main/mask/version有符号但不导出，官方两个模块各自链接gsl_point_id；参考源码存在gsl_point_id.c及对应Makefile规则。下一步应以F8专用驱动名/匹配避免内置GSL重复注册，链接自己的算法并验证目标ABI，不能复用旧6.1.172对象或直接强启禁用节点。
- 用户询问G2充电，已明确充电管理/BQ/CW禁用、USB-C/PD未验证，不能保证正常充电，先只刷回原BOOT再接充电器。日志已保全不影响接续；尚未确认本次回退，勿假定SSH在线。

下一步触摸模块/原厂r8 shuping profile + IRQ/复位/坐标映射 + KWin日志补采，保留G2已测GPU/内屏基线，新候选独立命名。充电仍是后续必须适配项，不能记录成已支持。无后台任务。

## 第二十九轮接续：G1 panic已定位，G2 GPU电源域修正候选就绪

- G1用户全程黑屏/无日志盘；主助手核实无Rockchip USB枚举、SSH无路由。用户已回原BOOT，SSH+collect-f8-g1-failure.py确认Arch/5.10恢复；只读采集/sys/fs/pstore console64794/dmesg67479字节，原始hash及来源在local/hardware/armbian-official-g1-failure-20261029-01/capture.json，未清空设备pstore。持久化日志确实跨此次恢复保留，不推及断电保证。
- pstore证明官方6.1.115实际启动、37秒进入Armbian Ubuntu systemd259，F8 model/hostname正确。33.848197秒vdd_gpu_s0被unused清理关闭；41.7519秒power-controller缺gpu-supply；41.763609秒GPU电源域上电失败，41.764651 panic_on_set_domain，调用栈Panthor init→platform probe/genpd attach→rockchip_pd_power。不是未执行Armbian或仅测试旧Arch GPU；EGL/KWin尚未执行。VOP无vop-supply/DVFS fallback、panel bpc0另记非致命待项，未混入本轮修复。
- 上版遗漏电源域消费端供电。官方精确Image/System.map验证rockchip_pd_power直接调用optional regulator get/enable再启时钟，6.1.172 PM参考源码另外明确版本标签保存。依据在official-gpu-baseline-20261029/g1-failure/failure-analysis.json及调用/源码摘录。未关闭panic保护或强制always-on。
- G2只给power-controller添加gpu-supply指向F8 DCDC_REG1（与Panthor mali-supply同轨），model更新G2；其余DT逐项完全相同，电压550–950mV/200MHz初测上限不改。官方Image/resource/2.15GB根及所有module/probe/helper字节不改，cpio只改init/报告版本标签与空FAT卷标。FAT/shell/FIT payload/12KiB布局/供电phandle读回通过。
- 新候选outputs/armbian/official-f8-graphics-g2/BOOT_ONLY_ARMBIAN_26.8.1_GPU_G2_CANDIDATE.img，49427380字节，SHA256 6afe593ffcdbeb5c1dbef48dc97b25caece51ac5de6f00288db57eba854c0f08，日志F8AG2。preflight hardware_fix_verified=false，尚未部署复测。G1 preflight/manifest已标hardware失败并留before-hardware备份，勿原样再测。
- 原Arch已恢复，设备已有官方根再次只读SHA验证a6a76aef…a6f5eb/2148360192一致，无重传/覆盖；初始上传报告另存tablet-root-staging-initial.json。stager修复复用时remote_path缺失字段，改“staging operation未执行镜像”命名，不覆盖pstore已证明G1真实执行的结论。

下一步按docs/armbian-official-g1-failure-and-g2.md只刷G2 boot，3–4分钟看F8AG2/内屏。若失败回退后新版本目录采pstore，勿覆盖G1证据。当前原系统可用，无后台任务/新设备写入/自动刷机，回退BOOT不变。

## 第二十八轮接续：官方 Armbian GPU/内屏候选可协调真机测试

- 用户要求开始。保留官方26.8.1根/内核/模块/Mesa/固件，F8 R5已测板级DT移植到官方GPU绑定；GPU子树取自本次官方DT，按provider物理路径重映射phandle并核对cells/reg，旧Mali disabled、Panthor okay，只有官方200MHz OPP启用。VOP/IOMMU→VP2→DSI0/panel供电/PWM14/背光启用，原1200×1920/160MHz时序不改，亮度32。GPU thermal cooling引用转向Panthor，charging/touch仍禁用。
- DT草稿首版raw字节DTS产生引用标记伪告警，改直接FDT序列化/DTB回读，二者最终字节相同。输出r1b DT SHA cc033202469d61ed18bbc6631d47ff8c99b7b1d6faa444c60da04bb7c3279fe0。29项与官方6.1.115显示绑定一致，新增DTC警告0；旧SoC/F8节点来源清楚记录，不冒称官方提供F8板DT。
- 官方独立根接入专用target、GPU/Wayland测试和110秒USB报告timer，UID1600 f8gpu密码锁定无sudo，PAM/logind真实DRM会话。其他板firstrun/自动扩容/USB2优化等mask，fstab无物理挂载，机器ID空、SSH主机密钥6文件从副本清理，无SSH/SDDM全桌面。完整5单元验证、实际ARM64 KWin --help检查通过。
- 严格GPU探针须Panthor render node/G610/实际像素/无软件renderer或libMali，GBM+surfaceless GLES3 RGBA8 FBO避免pbuffer假设；通过后才启动约25秒KWin/kdialog Wayland窗口。启动脚本清除DISPLAY/WAYLAND_DISPLAY/QPA嵌套环境，客户端明确Wayland；probe/report/helpers在RAM upper注入，精确哈希在boot-manifest。实际打包版本ARM64无GPU时拒绝通过，不是正向硬件验证。
- 官方根SquashFS2148360192字节，SHA a6a76aef7feae1d1eb89c615ccbede837d7b4fc657c790580273ef5a20a6f5eb；原Arch/5.10 SSH已实际恢复确认，新增上传/var/lib/f8-pro/armbian-official-26.8.1/rootfs.squashfs，94.5秒完成fsync独占发布和落盘后重读SHA。未改原配置/boot/GPT、无重启。tablet-root-staging.json记录，勿再传或覆盖。
- 唯一用户候选outputs/armbian/official-f8-graphics-r1b/boot-g1b/BOOT_ONLY_ARMBIAN_26.8.1_GPU_G1_CANDIDATE.img，49427344字节，SHA256 0eddfc105ff790687bc96a84cb580ffb1ca2ba6ee7823fa121beec2510943926。使用官方Image SHA a67daf71…0c37b7，runtime47316992/textoffset0，initramfs只含匹配官方squashfs/overlay ko，保留官方桌面cma=256M。FAT/FIT四payload/12KiB padded布局/回退hash验证通过，真实打包blkid和BusyBox modprobe -D模块依赖/逐字节配套通过；此BusyBox不支持-n，仅-D列依赖无加载。预检ready_for_user_coordinated_trial=true，未部署/无硬件测试。

下一步按docs/armbian-official-graphics-g1-test.md只刷boot，3–4分钟看F8AG1。采集GPU.JSON、GRAPHICS/WAYLAND/GFXSTATE/DRM/ARMBIAN/MEMINFO及旧日志，询问用户内屏/短暂测试窗口观察。首测不是完整Plasma/触摸/充电或性能测试；GPU通过与KWin renderer/物理画面分开判断。父目录和boot-g1a是保留的封装中间版本，不作本轮入口。无后台任务/本地挂载，原BOOT回退仍有效。

## 第二十七轮接续：官方根已准备，Panthor官方切换验证通过

- 已验签官方26.8.1 KDE镜像解压为8438939648字节，GPT header/table CRC通过；本地ro,noload检查并卸载。官方根用cp-a完整复制到/var/tmp/f8-pro-armbian/f8-official-armbian-26.8.1/rootfs，所有者/权限/符号链接保留，未与旧根hardlink，也未改原始镜像。
- 实读stable26.8.1、构建commit短值8b778f3d8（不同于参考框架pin），Mesa26.0.3、KWin/Plasma6.6.5、SDDM0.21。Panthor=m、对应ko与arm/mali/arch10.8固件均有，无libMali库。先前libmali_files宽泛匹配误含Mesa mali-dp/相机/Perl文件，工具已修正为libmali库名并重读为空。
- 关键发现：官方参考DT旧Mali=okay、Panthor=disabled，armbianEnv没有overlays启用项。官方panthor-gpu.dtbo已用fdtoverlay离线应用并验证旧GPUdisabled/Panthorokay/mali-supply解析正确；实际供电符号是RK806 DCDC_REG1。参考DT不是F8可刷DT，仍需板级迁移。
- 26.8.1 Image SHA a67daf71caefef6b97a22ba708bbb302b239a4a9b4874cadd17a217ebd0c37b7，Panthor ko SHA dde1617d0fb8c39fb04cb471d0eae28aab5afdbd71771605947d3c912604107f；G610固件SHA a27847ea11f8efb3136340c3ba8aab413ae25145eeb4a7f64ff5edd829a2405b。旧26.8.3 Image即使同uname也不同hash，不混用旧headers/extra ko或6.1.172模块。
- 官方根复制成功后overlay供电校验曾因硬编码节点路径失败，改从__symbols__解析后复用已完成copy验证成功；cp完成/卸载与后续prepared report独立记录，未覆盖根。inspect解压前缀校验续解也已完成。

下一步保留官方GPU整套，迁F8 DT/FIT/电源/内屏/触摸，明确Panthor启用并做render node/Mesa像素读回/Wayland实测。不再自建Debian根替代Armbian、不再新增纯PID1轮次。本轮无新F8 boot候选、无GPU硬件验收、无平板写入/重启，R5是否回原BOOT仍未确认。所有本地挂载已卸载，无后台任务。详见docs/armbian-official-baseline.md和official-gpu-baseline-20261029的3份主报告。

## 第二十六轮接续：正式Armbian KDE镜像基线已取得并验签

- 用户纠正目标：旧闭源GPU与新开源GPU不同，必须直接从Armbian开始。迁移主线切换到官网官方完整镜像，旧R1-R5仅是启动/基础用户态证据，不是GPU验收，不再安排同类纯PID1刷机。docs/armbian-official-baseline.md和migration首部已明确。
- 官方镜像Armbian_26.8.1_Orangepi5_resolute_vendor_6.1.115_kde-plasma_desktop.img.xz，1576708364字节，SHA256 fae6bd998cf8bf75274a367f1f3937aae609d6560e3110df35434cf6a9a45612。下载在downloads/armbian/official-desktop-26.8.1，官网选择有原始目录/页面证据；GitHub os/latest是trunk，未用作稳定基线。
- PGP Good signature/VALIDSIG指纹DF00FAF1C577104B50BF1D0093D6889F9F0E78D5，与官方文档一致；公钥/签名日志/下载报告在analysis/armbian/official-gpu-baseline-20261029/。
- inspect-armbian-official-desktop.py在WSL验签后解压；先前会话中断留5.3GiB official.img.part，确认无残留进程后改成锁定运行、完整重放校验已有前缀再续解，避免覆盖。解压后只读挂载镜像文件，读取包数据库、配置、Panthor固件/overlay与节点，不执行服务或维护脚本。当前内部审计尚待完成。

这是移植来源，不是可给F8刷入的整盘镜像。先保留官方GPU配套，迁移F8 DT/外设；如需改内核通过Armbian框架明确变更。原loader/GPT/Arch和所有R5/回退文件保留，没有设备写入/重启，R5是否回退仍未确认。

## 第二十五轮接续：R5 权限/基础服务真机通过，转向图形

- 确认F: F861R5，23份日志保全local/hardware/armbian-6.1-r5-20261029-01/。summarize-f8-fifthboot.py校验成功，test-result.json保存哈希/范围；docs/armbian-fifthboot-result.md记录实测。
- systemd PID1、8核、专用target active，SYSSTATE=running，FAILED=0。resolved以systemd-resolve正常active/running/result success；NONROOT的User=nobody读取测试exit0。根0755、3注入单元0644和旧hostkeyunit0644均实证，旧权限告警/200CHDIR在journal消失。
- 原p6 ext4 ro,norecovery，SquashFS完整SHA通过且ro，upper/work留RAM；hostname修正。无panic/Oops快照，末kernel消息约38.16秒，不是长期压力证明。
- DEVICES确认当前无DRM/Mali（图形仍禁用），regulatory.db确实缺失；RGA聚合/早期供电debug/libbpf和unmerged-bin提示仍在。DNS服务启动不等于联网DNS/SSH通过。

下一步从基础用户态转向VOP/VP2→DSI0、IOMMU、面板供电/复位/背光与GPU配置核对，准备实际Wayland图形候选，不再重复纯PID1短测。触摸/充电/DVFS尚待。日志已保全可只刷原BOOT恢复使用，尚无R5回退确认，勿默认SSH在线。没有设备写入/新镜像/后台任务。

## 第二十四轮接续：R5 权限修正版可协调短测

- 新fifthboot init明确upper0755后再mount overlay；3个注入单元0644、报告程序/目录0755、旧hostkey单元仅RAM overlay chmod0644。R4源/候选、冻结Image/SquashFS均不改。
- RAM hostname改f8-pro-eval，mask4个无关维护timer和systemd-pstore以减少无关活动/保全pstore，不mask resolved。新增PERMS/NONROOT/RESOLVED/DNSLOG/DEVICES快照；NONROOT临时User=nobody服务实际读取/etc/os-release。
- R5候选42120420字节，SHA256 57334c1970a7d17fc31c56ed524f1980c6e13babc2a63a6095f756b81d485d3c，outputs/armbian/firstboot-diagnostic-r5/BOOT_ONLY_6.1_DIAGNOSTIC_R5_CANDIDATE.img，卷标F861R5。DT无新增警告，ARM64 shell/blkid、FAT/cpio/FIT和padded布局、3单元依赖、5条挂载交接fixture通过；实际uid/gid65534 Linux权限fixture确认0700拒绝/0755允许读取。未实挂overlay或运行目标PID1。
- 工具builder/preflight支持r5，独立check-f8-r5-userspace.py；离线clone仍有lower旧hostkey单元告警，RAM中修正待真机证明。Windows生成shell换行问题已在构建阶段发现并修正为LF，成功候选已重新核验。旧候选未覆盖。

下一步按docs/armbian-fifthboot-test.md只刷boot短测，等待2–3分钟F861R5；验收权限/非root/ resolved状态后推进Wayland显示/GPU/触摸。无需重传rootfs。当前没有设备写入/重启、没有R4回退确认、无后台任务。诊断充电仍禁用，采集后可回原BOOT。

## 第二十三轮接续：R4 评估 systemd PID1 真机启动成功，权限问题待修

- F: F861R4确认，18原始日志已保存local/hardware/armbian-6.1-r4-20261029-01/。summarize-f8-fourthboot.py通过并生成逐文件哈希/test-result.json；说明docs/armbian-fourthboot-result.md。
- 目标Debian Trixie systemd257.13作为PID1、f8-evaluation.target active，8核在线。原p6 ext4 ro,norecovery，SquashFS SHA检查成功且只读lower，根overlay upper/work为RAM，未运行桌面或TCP SSH。
- systemd-resolved.service唯一failed，退出200/CHDIR并报journal socket Permission denied，整体degraded。init umask077新建upper默认0700，是根目录遍历权限问题的高概率原因；无target stat证据，下一版本明确0755并采集权限/服务状态。新注入units因cp/umask变0600，原SSHhostkeyunit权限过宽；在新RAM overlay中修，勿改旧镜像/硬链接树。无panic/Oops快照，不等于长期稳定。
- journal还显示常规timers、AF_UNIX本地SSH socket及pstore搬移；不是联网/完整服务验收。设备日期是内置epoch而非测试日期。后续收敛评估timers、修正hostname并验证固件/模块，继续Wayland显示/触摸准备。

日志已保全，用户可只刷原BOOT回退使用/充电；尚无此次恢复确认，勿假定SSH在线。R4与回退候选保持不变，无后台任务。

## 第二十二轮接续：评估镜像已暂存，R4 PID1候选就绪

- 只读SSH实际确认原Arch/5.10.160已经恢复、sudo可用和空间充足。937MB评估SquashFS新增到 /var/lib/f8-pro/armbian-evaluation/rootfs.squashfs，34.6秒完成传输/落盘后复核SHA a69fdacd…5a8dc，未覆盖旧文件/boot/配置，无重启。记录userspace/tablet-rootfs-staging.json。
- R4只读挂载原Arch作容器，校验镜像SHA、只读SquashFS，再以RAM upper/work做overlay，注入专用basic评估target/15秒timer/report服务后switch_root运行目标systemd PID1。无桌面/SSH/完整multi-user，不改变原身份或数据；目标产生的写入限RAM。
- outputs/armbian/firstboot-diagnostic-r4/BOOT_ONLY_6.1_DIAGNOSTIC_R4_CANDIDATE.img，42119728字节，SHA256 6adc48f275c1d42ea84287591e276a761e514b54d78fde232ff8b7bbd5c64b6c。Image未改，DT/shell/FAT/cpio/FIT/ARM64依赖/padded布局检查通过；目标单元独立验证通过，5条ARM64挂载交接失败回退fixture通过；没有真机PID1测试。
- verify对原镜像SSH hostkey单元有可执行/过宽权限告警；该旧单元不由本target启动，后续正式服务启用前需规范。新R4单元0644。不要chmod独立hardlink验证树的已有文件，以免改动共用inode的构建root；冻结SquashFS未改。

下一步按docs/armbian-fourthboot-test.md协调只刷boot测试，等2–3分钟检查F861R4，采集PID1/OSREL/MOUNTS/TARGET/FAILED/JOURNAL，随后回退原BOOT。未执行部署、无后台任务。R4数据镜像已在平板，勿重复上传或覆盖；旧首测/R2/R3/回退包保留。

## 第二十一轮接续：R3 8核与只读用户态达到目标

- 用户报告R3成功，主助手确认F: F861R3，21文件保存在local/hardware/armbian-6.1-r3-20261029-01/，test-result.json记录文件哈希；summarize-f8-thirdboot.py核验结论。CPU0-7全部在线、ttyS2注册并作为console，旧initial-console警告消失；不代表外接UART或DVFS/压力测试。
- 原p6实际以ext4 ro,relatime,norecovery挂载，Arch标记确认，true退出0，systemd262 --version退出0，随后正常卸载。仍有/etc/systemd/user.conf Function not implemented警告，未定位；不能冒称PID1/服务通过。
- dmesg快照至约8.95秒无panic/Oops。PARTS.TXT早于MMC枚举，不能据其缺MMC行判故障；后续dmesg/p6挂载提供证据。Armbian用户态、图形/触摸/充电仍未启动或验收。

下一步转入已构建Trixie评估rootfs的RAM-overlay/systemd试启动准备：需用户先只刷回原BOOT并确认原SSH可达，再将SquashFS新增到独立暂存目录，核验SHA，完善可观测日志和网络入口。当前尚未收到此次回退确认，不要把诊断FAT当原系统或尝试其SSH。说明docs/armbian-thirdboot-result.md；无后台任务或新镜像改动。

## 第二十轮接续：告警分类完成，R3 SMP/只读用户态候选就绪

- 固定 regulator core 证实现场 device-link ENOENT 是 create_regulator 中 sysfs 链接的 rdev_dbg/non-fatal 分支，不是供电 probe 失败或 device_link_add PM 链失败。RGA 聚合 rga_init 仍无条件绑定 IOMMU，诊断禁用核心不能消除该全局错误。没有为日志噪音修改内核。说明 docs/armbian-regulator-console-audit.md。
- 原厂 fiq UART2 pinctrl 实际为 m0（GPIO0_B6/B5 function10），R2两脚未占用。R3启用UART2并改ttyS2/1500000，替代未实例化的ttyFIQ0；实际注册/发送未测试。
- R3移除maxcpus=1，保留已验证的vendor cpufreq黑名单；合并8核启动和原Arch PARTUUID-checked ro,noload挂载/true、systemd --version限时检查，不启动PID1/服务，不做调频/压力/充电测试。
- outputs/armbian/firstboot-diagnostic-r3/BOOT_ONLY_6.1_DIAGNOSTIC_R3_CANDIDATE.img已生成，42118860字节，SHA256 16c32f21ab9deba9550b04a8933bbe22a4ffb2d61f2c196bce4dfa924c852000。DT无新增警告、shell/cpio/FAT/FIT与padded geometry检查通过，实际打包blkid依赖ARM64 QEMU验证通过。卷标F861R3，额外ROOTPROBE/RUNTRUE/RUNSYS/MOUNTS/CONSOLE/CPUPOSS结果。未部署。

下一步按docs/armbian-thirdboot-test.md协调用户短测，保存F861R3全部文件后回退原BOOT。旧三版本/回退镜像保留；原系统恢复状态仍未明确确认。本轮无真机访问、无后台任务，Image/固定源码配置未改。

## 第十九轮接续：R2 真机达到核心供电绑定目标

- 用户完成 R2 启动，Windows F: F861R2 已确认；15 文件保存到 local/hardware/armbian-6.1-r2-20261029-01/。summarize-f8-secondboot.py/test-result.json 保存哈希与结果，说明 docs/armbian-secondboot-result.md。
- I2C0 GPIO0_D1/D2 实际绑定 i2c0m2，SPI2 冲突消失。0-0042/43 均绑定 rk860-regulator，驱动与 summary 报两路大核供电800mV、约束550–1050mV；不是外部测量，也不证明负载/DVFS稳定。
- vendor cpufreq initcall 实际跳过；只在线CPU0，policy目录不存在。与R2隔离设计一致，不是OPP/SMP测试。No available vop及零大小logo/LUT告警在该快照中消失，RGA聚合绑定、regulator device-link ENOENT、console等仍待核查。
- dmesg快照到约8.2秒，无panic/Oops，不能扩大为长时间稳定或充电/桌面完成。日志已保全，可随时只写原BOOT回退；尚无本次恢复确认，勿默认SSH在线。

下一步检查regulator consumer/device-link与console，再准备受控OPP/多核或用户态启动。首测/R2/回退镜像未改，本轮仅读F:并写电脑记录，没有设备配置写入或后台任务。

## 第十八轮接续：R2 核心供电总线诊断包就绪

- 独立 R2 DT/日志 initramfs 已构建，未改 Image。I2C0 m2 修正加入实际打包 DT；保留单核并按固定源码/vmlinux 符号确认新增 initcall_blacklist=rockchip_cpufreq_driver_init，先阻止 vendor OPP 校准，验证 RK8602/3 绑定。实际黑名单效果未测。
- 诊断中关闭 display-subsystem/RGA 核心，删除零大小显示占位；增加只读 I2C driver、regulator/debug pinmux、CPU online/cpufreq 快照，额外等待5秒。卷标 F861R2，序列号 F8PRO61R2，与首测区分。
- outputs/armbian/firstboot-diagnostic-r2/BOOT_ONLY_6.1_DIAGNOSTIC_R2_CANDIDATE.img 已生成，40890232 字节，SHA256 17762adae7a830ffd72be3dd2842d5a6b124c24d1ad30738c06141616586d3a3。DT 无新增警告、shell/ARM64 applet/FAT/cpio/FIT 四 payload 及 padded geometry 检查通过；preflight 为可协调 R2，未部署或实测。
- builder 增加版本目录和拒绝覆盖已有 manifest，防止重建首测/R2 破坏证据。首测与原 boot 回退镜像重新校验哈希未变。详见 docs/armbian-secondboot-test.md；原首测日志和test-result继续保留。

下一步用户方便时按之前只写 boot 方法进行 R2，出现 F861R2 后采集新日志，再回退原 BOOT；需要明确区分当前卷标，不能把 F861LOGS 当新结果。用户原系统恢复状态仍未明确确认，本轮没有访问平板。当前无后台任务；桌面/触摸/充电仍不在此轮测试范围。

## 第十七轮接续：首次 6.1 真机启动通过预定范围

- 用户按步骤刷入后报告日志盘出现。主助手确认 F: F861LOGS，十个日志文件已复制到 local/hardware/armbian-6.1-firstboot-20261029-01/；test-result.json 保存文件哈希和结论。新内核 6.1.172/init、eMMC HS200 及 8 分区枚举、USB2 UDC/只读 RAM 日志盘通过；ramoops 注册成功。没有桌面/触摸/充电/SMP/DVFS或存储写入测试，不是全部硬件通过。
- 真机暴露 I2C0 默认 m0 与 SPI2 的 GPIO0-11 冲突。原厂为 i2c0m2 GPIO0_D1/D2；f8-pro-compute-power.dtsi 已修正并新增验证，DT 320 项检查通过、unexpected_warnings 为空。尚未真机复测，首测镜像未改。
- 大核供电/OPP失败需在 mux 修正后复查；RK860X已内建。cpufreq.off 参数未阻止 vendor OPP 探测，不能当作电压/测量路径完全禁用。显示/RGA无关联节点启用、零大小 logo/LUT、console 与 regulator link/RK806 状态告警仍待处理。见 docs/armbian-firstboot-result.md。
- 用户询问回退原 BOOT 维持供电，已明确可以立即恢复：日志已保存；只写原回退 BOOT，不动其他分区，恢复原 Arch 后确认充电/SSH。尚未收到恢复完成确认；不要假定真机已回到 Arch，也不要对诊断版尝试 SSH。

下一轮先验证 I2C0/核心供电修正，再逐项启用用户态和图形/触摸。首测候选 SHA98037112…49b496 和回退 SHA7e51e71f…b1dd1 保持，后续包必须新版本命名；旧四产物构建结果独立保存。当前无后台任务。

## 第十六轮接续：首测包与当前 boot 回退备份就绪

- 用户要求明确何时测试。范围收敛为最小 6.1 内核启动/eMMC 枚举/只读 RAM USB 日志盘，不等待桌面和全部外设，不挂载物理分区，不启动 systemd/SSH。新 DTS 使用原板身份、观测 RAM banks/vendor-storage 快照及 USB2 固定 peripheral；GPU/面板/触摸/充电策略等未启用。
- 已生成独立首测 FIT：outputs/armbian/firstboot-diagnostic/BOOT_ONLY_6.1_FIRSTBOOT_CANDIDATE.img，40889988 字节，SHA256 98037112b015172461c9eb776aba6b85acee8aa080ec74a08c8aba90dc49b496。DT 编译无新增警告，必要功能内建，ARM64 BusyBox/所需 applet、shell 语法、RAM FAT fsck、cpio/FIT 四 payload 哈希检查通过；包含 DT 12KiB 的布局筛查通过。
- 当前 /dev/mmcblk0p3 已只读完整备份到同目录 CURRENT-BOOT-ROLLBACK-64MiB.img，67108864 字节，SHA256 7e51e71f7ec7439357e5ea2fbb97118715fe5fcf10401b638609df33567b1dd1。本地/设备端哈希相同，PARTUUID/start/size 及四 payload 内部哈希验证通过；ramdisk 大小与当前 chosen initrd 跨度相同。
- preflight.json 标记 ready_for_user_coordinated_trial=true、deployment_authorized=false、hardware_test_performed=false。这是可协调的首测候选，不是硬件验收或完整 Armbian。USB PHY 强制设备模式已按固定源码检查，电气行为及新 payload 接受/最终 DT 修补留在受控硬件首测验证。

下一步与用户协调进入 Loader，按 docs/armbian-firstboot-test.md 只写 boot 测试、采集 F861LOGS 日志盘，再只写 boot 回退并验证原 SSH。现在需要用户安排物理连接/Loader 与本次临时覆盖 boot、重启的确认；没有执行部署。新候选与旧四件评估产物独立，原源码/固定配置和原根分区未改；没有后台任务。生成工具 build-f8-firstboot-diagnostic.py、backup-f8-current-boot.py、check-f8-firstboot-preflight.py。

## 第十五轮接续：前处理、DT 扩容及旧内核放置观测

- 原厂二进制核验 guard 查询 signature/required/conf，前处理的 FDT/kernel/ramdisk 对应三个 *_addr_r 环境变量；静态读取按十六进制、缺省 0 拒绝。尚未确认当次控制 DT/策略或生效环境内容。
- 后续 DT 重定位函数确实加 0x3000（12KiB），fdt_high 全 1 路径原地增大 totalsize，另一分支分配并展开。上一轮的后续 pad 不确定项已解决；实际 fdt_high、原地尾部容量和最终内存修补未解决。
- 布局检查纳入 12KiB 并新增跨 bank 边界场景，共 9 条合成测试通过；默认地址/旧 banks 的 padded geometry 无错误，仍不是新内核真实布局。
- 通过 SSH 只读查询旧内核 5.10.160：Kernel code 从 0x00400000 起、data 到 0x02aa0000（不含），首尾跨度与原 Image 的 40501248 runtime size 一致；chosen initrd 为 [0x0a200000,0x0a9b4ae0)。两个起点吻合内置默认值，但不证明新内核、环境值或 DT 地址。没有读 RAM/环境、写设备或重启。

说明 docs/armbian-loader-placeholder.md 第十五轮，报告 loader-placeholder/verified-handoff-paths.json、loader-layout-check.json、live-loader-placement-2026-10-29.json。下一步最终 memory/reserved-memory 修补与 DT 选择/生效身份、诊断通道及整板 DT。新内核尚未启动，四件封装产物/固定源码不变，无 FIT、无后台任务，boot_ready=false。

## 第十四轮接续：loader 占位地址原二进制核验

- 固定 Rockchip 官方 U-Boot 参考提交 1c535d65b8509f388d09e49fb6961f49fda35a1d，15 文件/240820 字节；不是已证明的本板固件源码。新工具 fetch-f8-loader-reference.py、inspect-f8-loader-placeholder.py、audit-f8-loader-fixup.py。
- 原厂 uboot.img 的未压缩 ARM64 payload（1312056 字节，SHA e6357ab74144e77790a71b39cd12746203dfb17a177889dcf19b9ec4e024a053）中，0x5998 函数的掩码/比较、非占位直接返回、guard 后节点与双写入调用结构已核验；占位解释不再只有参考推断。callee 名称部分仍为结构对应，guard 身份/签名策略未完全证明。
- 旧分配函数直接按 payload size 做 512 字节对齐，未见新参考代码的 FDT max+pad 分支；最终 bootm 扩容行为仍未知，不能套用新版分配假设。参考 board.c 还会改变生效环境地址，默认字符串仍不能当真实地址。
- 结果 analysis/armbian/loader-placeholder/verified-fixup-structure.json，说明 docs/armbian-loader-placeholder.md。源码与工具静态检查完成；没有执行 loader 或访问平板，boot_ready=false。

下一步定位真实前处理/环境使用、guard 和最终 DT 的扩容/内存修补，补可观测诊断通道与整板 DT。原 loader-contract.json 是第七轮历史报告，应与新报告一起读；四件封装产物、固定内核及真机未改，没有新 FIT 或后台任务。

## 第十三轮接续：触摸绑定与输入边界收尾

- 候选用 mutex 保证本驱动只有一个绑定实例；devm cleanup action 在 GPIO/input/IRQ 资源之前注册，使全局指针在资源回收后清除。拒绝第二实例，错误实例不能释放所有权；候选全部关闭旧可写 proc 调试接口，避免解绑后的遗留入口访问全局指针。
- 输入 cinfo 清零，原始/算法触点数检查、坐标和 ID 在窄化前校验，同帧重复 ID 仅报告一次。帧头改为 get_unaligned_le32，避免高位字节的有符号移位；读帧或算法反馈写入失败释放触点并停止本帧处理。
- 提取实际函数进行主机 pthread/UBSan 检查：绑定竞争仅一个成功、错误所有者不释放、释放后重绑及 17 个边界/错误帧场景通过。算法、input、I2C 为模拟对象，未测试真实 devres 回收或控制器算法。
- 最新 AArch64 完整驱动对象编译/内嵌数据检查通过；PM 4000 请求及传输 1252 故障注入回归通过。preparation、compile-check、pm-check、transport-check、binding-input-check 对应候选 SHA256 d7822db00ca3703a0ae439940b8eff1951dc87253db1476fc82e08f941220661。

触摸主要离线检查阶段收尾。下一步优先整板设备树/loader 交接与受控试启动前置条件，再在新候选内核中整合驱动；当前只是对象编译，尚未整核链接。目标配置还含其他 GSL 驱动，整合时必须避免它们共享 gsl_point_id 全局算法实例；本次单实例保护只覆盖本驱动。没有真机访问、节点启用、模块加载或部署，冻结四产物未改，仍无可启动整板 FIT。

## 第十二轮接续：触摸休眠协调与释放

- 独立候选新增每设备 PM mutex 和显示/系统两类休眠原因；仅两者都解除才恢复，失败保留可重试状态。F8 profile 使用独立 FB notifier，修复原辅助层丢失恢复错误及过早缓存状态的问题；通用注册路径保留。
- quiescing 阻止排空期间的输入 work 重新启用 IRQ，同步 IRQ/排空 work 后释放全部 11 槽及跟踪历史，不生成虚假按压；恢复失败保持非激活/IRQ 静默并复位拉低。remove 的 stopping 标记与 PM mutex 协调。
- 提取实际函数运行主机 C/pthread/UBSan：两种睡眠顺序、重复事件、三阶段恢复失败重试、notifier 错误/相同事件重试、IRQ guard 和合计 4000 次并发请求均通过。此为模拟调度/硬件，不是真实内核竞态或硬件测试。
- 完整 AArch64 驱动对象编译与内嵌数组核验通过；传输回归仍要求 306 条写入、12 段延时参数及 1252 次故障注入通过。候选 compile-check/pm-check/transport-check 应有相同 candidate_sha256。

详见 docs/armbian-touch-pm.md。下一步处理全局单例/算法共享和绑定生命周期，再查输入报告与候选整合。Wayland/DRM 是否发出 FB blank 事件、真实 PM/IRQ/GPIO 和算法行为仍待验证。没有平板访问、部署或新桥接请求；固定源码、配置、四件封装产物保持，触摸禁用。

## 第十一轮接续：原 Ubuntu 复用与触摸启动参数

- 用户询问是否可直接使用原 Ubuntu 驱动：明确优先复用源码、固件与板级参数；旧 5.10.160 模块不能直接用于 6.1.172。已检查本地原厂镜像/归档资产，未找到对应完整源码，不把目标源码当作原厂源码。说明 docs/ubuntu-driver-reuse.md。
- 收集固定目标 gsl_point_id.c/.h、tp_suspend.h 及有界原厂反汇编，见 touch-static/implementation-index.json。原厂 startup 从所选配置取算法指针并调用 gsl_DataInit，目标存在相同接口和配置解析；尚未证明算法实现相同。
- 原厂复位三段 __const_udelay 循环为 20/10/10 次，startup 为 10 次；常量与固定源码毫秒延时宏一致，静态推导标称 20/10/10ms 和 10ms。目标通用值为 5/5/5ms 和 5ms。报告 startup-contract.json 明确未验证真实时间。
- 候选专用 profile 已沿用这组原厂标称等待，通用 profile 不变；模拟测试新增成功路径 12 段延时参数检查。完整驱动对象和 1252 故障注入/306 条写入验证结果见候选目录同版 compile-check.json、transport-check.json。

本轮尚未改动 PM 状态机或触点释放；tp_suspend 辅助层的 FB 恢复错误处理/状态提交，以及 FB 与系统 PM 协调是下一步具体工作。没有真机访问、部署或新桥接请求，固定源码/配置和四件封装产物保持，节点仍禁用。

## 第十轮接续：触摸上传与错误处理

- 候选取消异步下载 work，init_chip 同步完成编程序列并向 probe/恢复路径传递错误；短传输返回 -EIO，负 errno 保留。清寄存器、复位、上传与启动逐步检查，内存状态读取失败直接退出，fw2buf 使用显式小端非对齐写入。
- GPIO 延迟探测/请求/方向错误保留，有效 GPIO 0/1 可使用；OF GPIO flags 不作为 IRQ trigger flags。原厂 r8 IRQ 请求指令独立核验 flags=1/thread_fn=NULL，报告 irq-request.json，尚无实时极性验证。
- FB 注册延后，probe 失败清理 workqueue；remove 设置 stopping 防止退出中的 work 再启用已释放 IRQ，随后释放 IRQ 并清理 work。PM 恢复失败保留待恢复标记。仍需核查单例、FB/system PM 并发和剩余生命周期，未宣称全部修复。
- 从实际候选提取传输/序列函数，以主机 C/UBSan 模拟：成功 306 条写入逐字节符合独立参考；1252 个负 errno/短传输注入全部在首次错误处停止后续事务。驱动对象另外交叉编译并保留内嵌数组检查；最终结果以候选目录 compile-check.json/transport-check.json 为准，应具有相同 candidate_sha256。

说明 docs/armbian-touch-transport.md。下一步核对原厂算法与复位/启动、状态读回、触点报告及 PM 并发，再考虑整合。没有新桥接请求、没有平板访问或写入，触摸保持 disabled，固定源码/配置与四件封装产物未改；无 FIT 或可部署整板镜像。

## 第九轮接续：触摸 profile 候选对象编译

- 独立候选 armbian/touch/candidate-r8-shuping/ 已生成 gsl3673.c/profile.patch；没有应用到固定源码。新增 OF profile 选择专用固件、算法初值、800×1280 坐标及原厂 GPIO 属性，保留原通用 profile。使用不同的评估 compatible，现有 gslX680_shuping 节点不会自动绑定，节点仍 disabled。
- GPIO 初始化错误会中止 probe，板级候选不创建调试 proc 入口；其余 IRQ、复位/上传流程和 PM 基本继承目标驱动，尚未证明板级运行兼容。不能忽略全局单例、生命周期和上传错误处理的后续审查。
- 4851 条固件验证为 147 个完整的页选择+32 字连续数据页，符合继承上传循环的分批结构。完整驱动对象在固定 6.1.172 构建环境编译通过，无诊断；源基线核对一致，AArch64 对象中的固件/算法两数组与原参考逐字节相同。对象 SHA256 487311cf20906bda35e8e5099d50b59519ead50365e74de99932954d9a1bc4a4。见目录内 compile-check.json、build.log。
- 本轮桥接 touch-profile-review 返回 completed 但 output=[]，调用器标记 failed_empty_or_incomplete；没有有效意见、没有重试或待处理后台请求。上游报告输出 8452 tokens，超出请求 1200，不能依赖该参数作硬预算。编译及核验均由主助手本地完成。

下一步核查算法 ABI/实现、复位时序、IRQ 和 PM、错误处理，再考虑候选整合。未链接或加载模块、未更改固定配置/源码和四件评估产物，没有 FIT 或真机访问。本轮桥接补丁审查状态见 analysis/armbian/bridge-review/touch-profile-review.status.json；原厂 Arch 及恢复路径保持。

## 第八轮接续：触摸板级固件分派与参考数据

- 只读 SSH 确认 gslX680_r8/gslX680_shuping，并仅通过 EVIOCGABS 查询原始轴范围 800×1280，没有读取事件流、原始 I2C 或内核内存。物理面板 1200×1920 不能直接作为触摸原始范围。
- 归档 Image 解码 71364 个静态符号，全部 58 项实时符号相对 _stext 偏移吻合；Image 头分支独立佐证 _stext 文件偏移 65536。通过注册描述符→OF data→probe/load_fw 静态路径，确认 shuping 选择独立 4851 项/38808 字节固件及 512 个 u32/2048 字节算法初值，与此前仅证明存在的通用 GSL3673 表不同。没有读取或证明运行时可变算法内容。
- armbian/touch/reference-r8-shuping/ 已保存原始字节、C 参考头和来源哈希；使用目标实际 struct fw_data 声明进行 AArch64 独立单元编译，sizeof=8，导出的两数组逐字节一致。不是完整驱动构建/上传/硬件验收，参考头没有接入内核或 rootfs，触摸继续 disabled。
- 详见 docs/armbian-touch-dispatch.md；证据 analysis/armbian/touch-static/firmware-dispatch.json、reference-compile-check.json，真机元数据 touch-input-metadata.json。vmlinux-to-elf 1.4.0 与依赖仅安装在项目 tools/vendor-lib。
- 本轮桥接 touch-dispatch-review 请求 HTTP 502，未取得审查意见，没有当作完成或反复重试。调用器新增每任务 .status.json，后续可区分 running/completed/失败；本次失败已单独记录。

下一步在独立候选补丁核对并接入板级 profile，适配 GPIO、复位/上传顺序、算法调用、坐标/IRQ 和 PM，再做驱动构建。冻结的四件评估产物不变，没有 FIT/新后台构建，没有真机写入、刷写或重启。整板 loader、充电/USB-C、显示/GPU/键盘及首用户流程仍待完成；原 Arch 恢复路径保留。

## 第七轮接续：loader交接与静态布局审查

- 继续调用responses-bridge完成小范围loader证据审查，结果loader-contract-review.txt/.json；主助手核对原始资产、固定内核启动规范及U-Boot上游签名文档，没有直接执行外部模型建议。
- 原厂启动资产和FIT payload哈希/偏移边界重新通过。原/新Image头text_offset=0、flags=0xa，但原厂FIT的0xffffff00/01不能按字面加载；其范围不在旧DRAM观测内。0xffffff02仅来自历史ramdisk包装，不是原UbuntuFIT条目。
- 归档U-Boot内置默认kernel/fdt/ramdisk地址已提取，按旧banks及新运行尺寸做几何筛查无错误；这不是生效环境/交接地址。8条合成布局测试通过，报告仍boot_ready=false，未验证完整保留区与最终DT修补/缓存属性。
- 记录原板F12-v11根身份与当前compile-check包装身份的区别；完整固定源码没有F12板文件。扫描归档4个FDT候选未发现/signature公钥子节点，但未证明控制DT选择或签名策略，不能推断secure boot状态。
- 新工具tools/audit-f8-loader-contract.py、tools/check-f8-loader-layout.py；报告analysis/armbian/loader-contract.json、loader-layout-check.json；说明docs/armbian-loader-contract.md。没有生成/更改FIT，没有启动后台构建或访问平板。

下一步补齐loader实际解析/重定位、最终DT内存修补与控制DT/验签证据，并继续整板硬件适配。第六轮四产物及哈希保持不变，仍不可刷写或据静态检查声称启动通过。

## 第六轮接续：桥接协作与自定义评估封装完成

用户要求先尝试通过已启动的responses-bridge继续移植。主助手已调用配置的qiniu/conatus-free进行只读协作，没有改Codex provider或给上游工作区/SSH工具。较大请求返回completed但正文为空，未当作完成；缩小为文件系统函数任务后返回有效草案，已复核、修改并采用。调用器现在会拒绝空/未完成正文，不无限重试。详见docs/responses-bridge-review.md。

- evaluation-init.sh新增fs_available/ensure_fs：已有内建/已注册文件系统则跳过modprobe，否则加载并再次确认。复核时纠正草案将nodev列当文件系统名的边缘情况，保留失败诊断，增加rootfs模块release检查。原容器ro,noload、PARTUUID/GPT/SHA/marker及RAM overlay保护保持。ARM64 BusyBox5条fixture路径测试通过，无实际加载模块或挂载。
- 自定义Wayland SquashFS已生成并通过内容验证：936,742,912字节，SHA256 a69fdacdc7ad5fc1d9239ffb271c40bb2e05fb151e0635c2f59b2ef70885a8dc；含唯一6.1.172的2279模块，关键模块哈希、空machine-id、无主机私钥、Wayland会话/主题检查通过。原官方最小镜像保留。
- 匹配6.1.172 initramfs已生成：2,242,576字节，SHA256 e065e5f114c3920a5648975b3dfe464099fa7a2fd43600ca26e4b8b696c02d91；核对Image/.config/release/rootfs哈希与ARM64工具/newc归档。SquashFS/overlay内建，不带任何ko，和官方候选包分目录。两产物Windows/WSL哈希一致。
- Image+initramfs小计41,714,192字节，未含DTB/FIT/对齐。四产物配套清单outputs/armbian/evaluation-custom-set.json；说明docs/armbian-custom-evaluation.md。官方6.1.115产物没有覆盖。

本轮所有构建为本地离线评估，没有访问平板、部署/刷写/重启或新内核硬件测试。仍无可部署整板DTB/FIT，loader内存修补、充电/USB-C/触摸、GPU/显示/键盘、首用户和持久状态方案未完成。SDDM/KWin候选配置仍未启用。不要将归档检查当启动通过。下一步核验整板/loader与受控启动前置条件；继续桥接协作时优先给小而明确的审查任务，主助手必须核验输出。

## 第五轮接续：模块打包及桌面离线验证

- Breeze主题及依赖已补装成功；全部最新显式包已配置。离线验证确认4个主要程序为AArch64，Plasma Wayland会话、Maliit入口、Breeze和Qt6键盘插件存在。Plasma包附带X11会话入口，已在隔离root使用dpkg-divert可恢复改名保留；没有安装kwin-x11。
- 自定义2279模块已完成去调试信息/全架构与vermagic检查/depmod全符号版本检查，关键CW/BQ/Panthor版本符号37/48/233项匹配。归档26,618,696字节，SHA256 d98a2ad8de3b4343a861a652ada1838150d542c94baebf2a4ac8d2715b190f08，路径outputs/armbian/evaluation-kernel/modules-6.1.172-f8-pro-armbian-eval.tar.gz，Windows/WSL一致。
- 模块已配入隔离Wayland根目录，逐文件哈希及depmod符号验证通过。旧6.1.115树移动到/var/tmp/f8-pro-armbian/retained-wayland-official-modules保留，桌面只含6.1.172模块树。原最小rootfs/SquashFS/官方候选initramfs保持独立。
- 隔离root构建SSH主机密钥6文件已清理，machine-id为空；加入ssh.service依赖的目标ssh-keygen -A服务，离线unit校验通过，服务未运行。现有真机、客户端SSH私钥与known_hosts无改动。
- 说明docs/armbian-module-bundle.md，报告analysis/armbian/kernel-build/verified-custom-modules.json、userspace/custom-module-staging.json及identity-sanitization.json。桌面包验证报告verified-wayland-packages.json在模块/身份整理后重跑。

尚无自定义6.1.172配套initramfs和新桌面SquashFS/整板FIT。SDDM/KWin候选配置仍未启用，GPU/内屏/键盘等无新内核实测；充电限制/IRQ及USB-C、触摸、首用户流程等仍待适配。不得把模块/包离线验证当整板功能完成。本轮只操作本地评估目录，没有访问平板。

## 进度查询：两个后台任务均已成功结束

2026-10-29只读检查确认：modules-build.exit=0，完成于香港时间08:28:40，完整Module.symvers已导出（1,242,877字节）；Wayland安装wayland-install.exit=0，完成于08:58:35，wayland-packages-installed.ok存在。未发现make/apt-get/dpkg/modpost进程。包清单确认Plasma/KWin6.3.6、SDDM、Maliit及PipeWire已安装到隔离根目录，日志包含policy-rc.d阻止服务启动。

尚未开始模块安装/打包及全量ABI验收；Breeze主题不在本次已安装清单（运行时采用补主题之前的旧清单），下一步先补主题再执行verify-f8-wayland-root.py。候选输入配置尚未启用，未生成新桌面SquashFS、整板DTB/FIT，也无新内核启动或Wayland/GPU/键盘实测。以下第四轮及更早的任务进行中状态已过时。本次仅查看进度，没有启动新安装或改动平板。

## 第四轮接续：Wayland 输入配置修正

- 已核对SDDM包版本为0.21.0+git20250502.4fe234b-2/Qt6；对应上游源码在Wayland下主动清空qtvirtualkeyboard设置。旧候选已改为KWin以--inputmethod启动Maliit，InputMethod留空，greeter合成器局部KWIN_IM_SHOW_ALWAYS=1。另准备桌面kwinrc默认输入法候选。配置未安装/启用，无输入或焦点实测。
- --no-install-recommends导致原计划未装Breeze主题，现包清单显式补入sddm-theme-debian-breeze。主题两包已单独下载并按签名索引SHA256核验/解包，QML和候选配置源码审计通过。见docs/armbian-wayland-input.md和analysis/armbian/userspace/input-method-audit/audit.json。
- 当前正在运行的APT不包含刚补入的主题。结束后先查实际结果，再运行原install-f8-wayland-root.sh补主题，然后运行已准备的verify-f8-wayland-root.py核对完整最新包清单/ELF/会话。不要并发APT，不把旧完成marker当新增主题验收。验证器目前未执行最终根目录检查。
- 模块编译已过MODPOST并进入.mod.o阶段；桌面在解包。曾观察到磁盘I/O压力较高，主机/WSL空间充足、无内存压力，检查未发现内核I/O/EXT4错误；稍后两个日志均继续变化。没有中止进程或重启WSL，继续检查session50506/37801与持久状态。

本轮未访问平板。仍无可部署整板DTB/FIT、新桌面SquashFS或Wayland/GPU/键盘实测。

## 第三轮接续：电池与充电兼容性

- 新增 f8-pro-battery.dtsi：CW2015原厂64字节曲线、2000ms周期、BQ供电引用及全部原厂数值充电参数；两节点保持disabled。没有把旧OTG regulator子树冒称目标可用接口，FUSB302通知引用暂未接入。
- 最新集成DT验证318项通过，unexpected_warnings为空；电池曲线逐字节一致，GPIO/供电/PHY引用校验通过。旧269/299项为历史。
- 充电源码审计发现目标不读取7项原厂输入/充电限制属性，不直接读取extcon/otg-mode-en-gpios，PD worker也需补板级上限约束。原厂4.2V max-charge-voltage与4.4V battery-regulation-voltage的有效策略、IRQ GPIO0/3_D5差异及FUSB302/OTG/PHY链尚待适配。原厂graph含异常remoteAudioService.java-endpoint，不盲目复制。详见docs/armbian-battery-charger.md和analysis/armbian/charger-policy-audit.json。
- 本轮仅只读SSH查询IRQ/GPIO及公开power_supply属性；快照位于analysis/armbian/live-charger-*-2026-10-29.json。没有充电设置、GPIO、模块或设备树写入。公开constant_charge_voltage读数不能作VREG设定证明，详见文档语义说明。
- 检查时自定义全模块编译及隔离Wayland桌面仍正常运行，未见构建退出结果。继续查session50506/37801或持久日志/marker，不重复启动。桌面尚在dpkg解包，不得打包半配置根目录。尚未生成自定义匹配模块包或新桌面SquashFS。

自定义Image仍为已验证6.1.172-f8-pro-armbian-eval；未更改内核配置/源码。官方6.1.115最小评估rootfs/initramfs继续独立保存；整板启动与Wayland/SDDM/键盘/GPU实测仍未完成。

## 第二轮接续：Image 已完成

本节更新取代下方上一轮的构建中信息。

- 自定义 6.1.172-f8-pro-armbian-eval ARM64 Image 编译成功并导出到 outputs/armbian/evaluation-kernel/Image，39,471,616 字节，SHA256 9089662ee0fe0c77eb6335b486a4b2312df28e5059238949960a94251703e25d，WSL/Windows 一致。ARM64 头的运行内存尺寸为 40,239,104 字节；核心符号表 vmlinux.symvers、System.map、配置和哈希报告已导出。报告 analysis/armbian/kernel-build/verified-evaluation-image.json。
- 旧 wrapper 在 Image 成功后误复制尚不存在的 Module.symvers 而返回失败；已确认失败点是产物导出，使用新导出器完成核验。tools/build-f8-evaluation-kernel.sh 已修复，并与模块构建共用 flock。不得将这次 wrapper 退出 1 解释为编译失败，也不得伪造原命令退出 0。
- 已启动 tools/build-f8-evaluation-modules.sh 编译全部同 ABI 模块，工具 session50506；日志 /var/tmp/f8-pro-armbian/kernel-config-build/evaluation-modules.log，持久状态 analysis/armbian/kernel-build/modules-build.*。完成后才会导出真正完整 Module.symvers。尚未安装模块或打包自定义 rootfs。
- CPU OPP 静态核查完成：候选 24/32/32 项，原厂 17/23/23 项，全部电压变体的目标值未超出本机稳压器范围。共有 OTP 校准单元的地址/长度/位域一致。低温与分档差异记录在 analysis/armbian/cpu-opp-audit.json，说明见 armbian-compute-memory.md。没有运行时分档、DVFS 或温控验收。
- 新增无线/RTC 禁用草稿 f8-pro-wireless.dtsi；集成设备树验证增至299项，全通过，unexpected_warnings为空。AP6275P 的 PCIe2x1l2/combphy0、GPIO、蓝牙 UART9 和 RTC 32k 时钟引用均核对；RTC、Wi-Fi/BT、PCIe/PHY/UART保持 disabled。详见 armbian-wireless.md。
- 原无线固件5文件及蓝牙 helper 按历史 SHA256 校验后整理到 /var/tmp/f8-pro-armbian/wireless-assets，含目标目录默认名及大小写候选软链接。报告 analysis/armbian/wireless/verified-assets.json。仅候选资产，不在桌面根目录，不启用服务，不含旧5.10模块。
- Wayland 由模拟进入实际隔离安装。新目录 /var/tmp/f8-pro-armbian/rootfs-trixie-wayland 从最小基底完整克隆；原 rootfs-trixie-evaluation 及其 SquashFS 不变。扩充显式包清单，包含 PipeWire、电源管理、网络/蓝牙界面、KDE授权代理、portal、IIO代理和Qt6 Wayland；不装 kwin-x11。签名APT update和新依赖模拟完成，目前下载后进入解包，工具session37801，日志 /var/tmp/f8-pro-armbian/wayland-install.log。policy-rc.d阻止服务启动，proc为私有只读挂载，结束会卸载。

恢复时先检查两个后台任务，勿重复编译/并发APT。桌面完成标记为 /var/tmp/f8-pro-armbian/wayland-packages-installed.ok；状态和日志最终复制到 analysis/armbian/userspace/wayland-install*。包安装完成不等于KDE、SDDM键盘和GPU通过。打包桌面镜像前仍须清理构建生成的machine-id/SSH主机密钥并设计首次启动生成流程，不能把构建期身份复制到设备。

本轮未访问或改写平板。仍无可部署整板DTB/FIT；官方6.1.115候选initramfs/rootfs不与自定义6.1.172混用。

## 本轮完成

- 旧源码补全进程已不存在，原工作区仍为稀疏检出。新增 tools/resume-f8-kernel-source.sh，带 flock、600 秒超时及持久化日志；重试成功，固定提交 85233a85b67928000afc2e966bab86a8c414f1b4 已完整检出，工作区干净。analysis/armbian/kernel-build/source-completion.exit 为 0。
- 最新设备树验证重跑通过：269 项原厂参数比对，扬声器 GPIO 语义迁移断言通过，报告新增 speaker_gpio_migration_verified=true；unexpected_warnings 为空。6 条零地址占位区警告与原厂对照相同。音频、显示、触摸与两个 GPU 节点依然禁用。
- 官方 6.1.115 的候选 initramfs 已实际生成并通过离线检查，不再只有脚本。产物 outputs/armbian/evaluation-initramfs/initramfs-6.1.115-DO-NOT-BOOT.cpio.gz，2,423,321 字节，SHA256 42db425e19cf8219cb1bba7b592e00eba2adf13376687cfcd90156e2ce41bfbe；Windows/WSL 哈希一致。
- initramfs 包含 ARM64 静态 BusyBox、ARM64 blkid 及精确依赖，以及官方相同 ABI 的 squashfs.ko / overlay.ko。BusyBox 包与隔离根目录已验证 APT 索引的 SHA256 一致；目标工具通过 QEMU 检查，modprobe 只做 -D 依赖解析，没有加载模块。newc 实际归档内容、root 所有权、链接及 console/null 设备号已检查，临时宿主 QEMU 未打包。
- init 脚本检查 uname release、systemd.gpt_auto=0、原分区 PARTUUID、Arch 容器标记、SquashFS SHA256 和 evaluation 标记；原分区仅 ro,noload，写层为 RAM。容器/下层挂载位于 /run 下，随 switch_root 保留；缺条件则停止，不切换回旧 Arch 用户空间。
- 官方 Image + 此 initramfs 小计 48,985,113 字节，小于 64 MiB boot 分区；尚不含 DTB、FIT、签名/对齐，不能据此称刷机包完成。仍没有与官方 6.1.115 完整匹配且可启动的 F8 板级 DTB，也没有 FIT。

## 内核构建状态

完整源码就绪后，已启动 tools/build-f8-evaluation-kernel.sh：基础源码实际版本 6.1.172，后缀 -f8-pro-armbian-eval。当前构建日志为 /var/tmp/f8-pro-armbian/kernel-config-build/evaluation-image.log，工具 session 61384。恢复时先检查实际进程和日志，不重复启动。

注意 Image 目标与完整 modules 构建不同。目标源码 scripts/Makefile.modpost 显示 Image 阶段输出 vmlinux.symvers；完整 Module.symvers 需要模块阶段。旧构建脚本结尾直接复制 Module.symvers 的逻辑需要在本轮构建结束后修正，不能把缺该文件误判为 Image 编译本身失败，也不能把 vmlinux.symvers 冒称完整模块符号表。已准备 tools/export-f8-evaluation-image.py，待 Image 结束后执行，检查固定提交/release/ARM64 头并按真实名称导出 vmlinux.symvers 和哈希报告；该导出脚本尚未用最终 Image 执行。完整 6.1.172 模块尚未构建，不可使用官方 6.1.115 模块搭配该 Image。

## 音频现场核对

2026-10-29 只读 SSH 再次确认 7-0011 的 name 为 es8388，实际 driver 为 ES8323，ALSA card 为 rockchip,es8388-codec。这只是绑定核对，没有播放/录音或设备写入。

完整目标源码同时包含 es8323 和 es8328-i2c 两个驱动，后者也匹配 everest,es8388。原厂双 compatible 可能导致目标绑定差异，不能仅按芯片名字删掉 es8323 fallback。两个候选驱动均在当前配置启用，音频节点继续禁用，后续需明确目标驱动选择及寄存器/初始化差异。multicodecs 的 Speaker 事件通过声卡 spk-con GPIO 控制功放；当前迁移保留原 GPIO4_A5 高有效。原厂缺少 hp-det 与 ADC 检测属性，不猜测添加插孔检测引脚。

## 下一步

1. 检查 Image 编译结果，修正产物导出与符号表标记，保存 release/架构/哈希；再准备独立的匹配模块构建。
2. 完成整板启动必需的 DT、loader 内存回填、CPU OPP、温控、PMIC 与启动封装核验。所有 DO-NOT-FLASH / DO-NOT-BOOT 产物继续只在本地。
3. Wayland 桌面仍只完成依赖模拟，尚未安装完整桌面，SDDM/键盘和 Panthor 无新内核实测。触摸固件选择、Wi-Fi/BT、USB-C 充电通知、音频、摄像头、传感器旋转和首启账户向导仍需适配。

平板仍是原 Arch/5.10.160；本轮仅只读 SSH 查询音频绑定，没有部署、刷写、重启、调压或加载候选模块。SSH 方式见 docs/f8-ssh-connection.md。
