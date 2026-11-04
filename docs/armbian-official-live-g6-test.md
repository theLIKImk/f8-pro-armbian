# G6 Wi-Fi SSH 与动态启动状态页（2026-10-29）

2026-10-30更新：r5已真机Wi-Fi SSH/插拔识别通过，ADC后台刷新已在r5 RAM修复；最新持久化候选改为official-f8-live-g6-r6（50080260字节，SHA839dff537aceda1f8aa7ca0b92f6f31ec2fa1e6d4c8b6026bda029d57e06106d）。r6未实际刷入；当前可继续使用RAM修复而无需立即重启。最新说明armbian-power-sampling-fix-2026-10-30.md，下文r5入口为历史发布记录。

用户要求启动SSH后改接充电器远程读取，若正常则作为后续测试BOOT，并显示TIME/POWER/F8 RK3588S PAD及闪烁BOOT。G6已实现候选，联网、显示和真实SSH登录仍待真机。保持官方Armbian/Panthor/Wayland路线，原根SquashFS不重传。

## 唯一试验入口

使用 **official-f8-live-g6-r5**。r4已进入systemd，但新target安装路径错误使联网/SSH服务未启动；r5修复安装路径并移除自动弹窗。

outputs/armbian/official-f8-live-g6-r5/BOOT_ONLY_ARMBIAN_26.8.1_LIVE_G6_CANDIDATE.img

50077396字节；SHA256：

`3768f600bb84e1be2cd18b3895e0e762effbf365600969e258074ca5288265c9`

仍只刷boot，起始LBA0x00008000，原分区0x00020000扇区，不刷其他分区或擦除。原BOOT回退文件不变。

## 已实现

- 基于真机通过G5，只启用无线平台节点、原厂PCIe fe190000及combphy0 fee00000。Wi-Fi电源/唤醒、PCIe reset/PHY及pinctrl物理引脚/电气配置逐项与原厂比对；BT/RTC、BQ/CW驱动继续禁用。
- 使用精确官方26.8.1 bcmdhd模块，已核验firmware_path/nvram_path参数与modprobe依赖；原AP6275P固件/NVRAM/CLM/config按归档哈希核验，含驱动需要的相对文件名链接，不加载原5.10模块。
- 在systemd basic.target之后，由f8-live-prepare.service把原Arch只读容器内的NetworkManager配置复制到RAM并关闭扫描MAC随机化、保留硬件MAC。早期init仅用BusyBox复制公开固件，不执行目标系统账户/SSH工具。镜像不包含Wi-Fi密码。实际SSID/密码不会写入配置阶段日志。
- RAM创建测试用户 **f8test**，复制原alarm公钥到其authorized_keys，关闭密码/交互认证和root SSH，测试sudo免密；保留原设备SSH主机身份，私钥只从原Arch读到RAM，不打进镜像。独立f8-live-ssh.service，不解除官方默认ssh服务mask。显式启动systemd-user-sessions，避免custom target缺少开放非root会话步骤。
- power-current.json约每10秒更新，只读BQ/CW，无配置值写入/复位/ADC转换/PD或OTG使能。固定文件覆盖，不无限累计RAM日志。
- tty2状态页：[TIME]显示真实运行时长，[POWER]显示CW电量及单读电压，中间F8 RK3588S PAD，下方[BOOT]每0.5秒切换显隐；再显示[SSH]当前IPv4及用户名。面板驱动初始化后才可显示，并非上电第一帧。按用户要求取消自动KWin/弹窗测试，启动仅加载GPU/面板/触摸驱动及无界面的GPU像素检查，不抢走状态页；最终桌面仍按Wayland路线适配。
- 备用只读RAM日志盘F8AG6，timer从210秒缩到100秒，预计上电约2–3分钟出现；联网SSH不依赖等日志盘。快照关闭FAT后才导出，不在Windows挂载同一FAT时继续写入。SSH可继续读取RAM中的实时JSON。

## 验证与限制

2026-10-30：r4的49文件已存local/hardware/armbian-official-g6-r4-20261030-01。systemd已启动，AP6275P固件/NVRAM/CLM加载和wlan0注册成功，原MAC恢复；GPU硬件检查通过。但IP为空、22端口未监听，SETUP/LIVELOG无条目。静态回查发现init安装循环只识别*.service|*.timer，新增*.target落入辅助脚本目录，因此仍使用旧图形试验target，所有新live服务未被拉起。不能把用户看到的Network connection timeout直接认定为DHCP/密码故障。

r5安装循环补*.target，并在离线验证中提取最终CPIO内真实init安装循环，用ARM64 BusyBox执行到隔离目录，确认新target实际位于etc/systemd/system。服务图检查也改用这份实际安装结果，避免此前手工把文件放到正确位置的验证遗漏。自动弹窗及触摸110秒记录取消，保留驱动与无界面GPU检查。其余内核、设备树、固件、充电策略不变。r5尚待真机网络/SSH/屏幕验证。

r3的14份日志已存local/hardware/armbian-official-g6-r3-failure-20261029-01。固件复制已不再报错，但目标rust-coreutils 0.8.0在rustix auxv初始化unwrap失败并Aborted。从脚本看最可能为chroot chown，旧版缺少阶段标记，不能声称已证明具体调用；早期chroot未挂/proc是相关环境差异。r4从设计上撤去所有早期目标程序调用：私有网络/账户/SSH配置移到正式systemd服务中，此时虚拟文件系统均就绪。只有网络/SSH服务依赖prepare，图形/状态页/报告不依赖其成功，避免一处配置失败使整机停在init。SETUP.TXT加入逐阶段记录，不打印凭据。

r4在隔离环境先用实际BusyBox完成固件链接覆盖及全文件字节比对，再在/proc、/dev、/run齐备时运行账户配置和真实ARM64 Rust chown/sshd -t/-T，全部通过；报告analysis/armbian/live-g6/setup-fixture-systemd-r4.json。最终服务依赖/FIT/CPIO/FAT/shell/布局已重新校验，实际ARM64板上行为仍需重测。原官方根、内核、DT及充电策略不变。

r2的14份早期失败日志已存local/hardware/armbian-official-g6-r2-failure-20261029-01。STEPS明确BusyBox cp -a创建已有nvram_ap6275p.txt链接时报File exists，尚未交接systemd，因此屏幕页和SSH均未启动。PCIe Gen1 x1已建链，只代表PCIe物理链路，不代表Wi-Fi已联网。r3改为逐个已知固件条目在RAM overlay删除原同名条目再复制，不递归删除目录，也不改原Arch或冻结根。新增使用实际initramfs BusyBox sh及cp/rm/mount等工具的隔离测试，预置同名链接冲突后初始化/sshd验证通过，见analysis/armbian/live-g6/setup-fixture-busybox-r3.json。先前GNU cp测试未覆盖BusyBox行为，不能当作这处问题的有效预检。r3仍待真机验证。

隔离overlay使用虚构Wi-Fi/公钥/主机密钥，执行真实ARM64 useradd、sudoers检查和sshd -t/-T，确认关闭密码/root登录，授权文件0600；实际官方根未更改。结果analysis/armbian/live-g6/setup-fixture.json。此测试不冒称真实SSH认证或无线已连接。

最终名称的服务/目标/timer在私有overlay整体验证通过；宿主systemd比目标旧，只对基础单元的新键产生忽略警告，无新增单元错误。ARM64 Busybox shell、CPIO不重复路径/受限差异、固件哈希、FIT四负载及内存区间/分区检查通过。G6预检hardware_test_performed=false，未刷设备。

## 测试次序

1. 先连接电脑USB启动G6，看状态页是否出现及[SSH]地址；未知IP不要默认旧.227仍可用。原Arch配置需仍在设备上。
2. 将地址告诉助手，先通过原专用密钥核验Armbian/6.1.115身份、SSH和当前只读供电JSON。若联网失败，等F8AG6盘，保存IP.TXT、NETWORK.TXT、PORTS.TXT、LIVELOG.TXT、DMESG及原POWER/GPU/TOUCH日志。主机名/IP和网络日志按私有硬件证据保存。
3. SSH连通且采样正常后，用户再将数据线换为充电器，保持Wi-Fi连接。读取前后电压、状态、电量，持续观察；当前ADC旧样本和CHG使能都不等于实际充电电流，本版仍未适配可验收的充电控制。
4. GPU/触摸/屏幕、Wi-Fi重连、SSH、插充电器后的供电行为通过后，才提升该BOOT为后续测试基线。当前仍是候选；高压快充、OTG、长时间充电/休眠未验收。

Windows连接：tools/Connect-F8-Live.ps1 -Address <屏幕IP>，用户f8test。该脚本使用WSL既有专用密钥，HostKeyAlias=192.0.2.227沿用此前已知主机身份，即使DHCP变化也不自动信任陌生密钥。不要改成关闭主机验证；若身份不匹配先核验。

助手可用tools/ssh-f8-live.py --address IP --script tools/read-f8-live-power.sh --sudo读取当前快照。原连接脚本alarm仅适用于原BOOT，不要混用账户。
