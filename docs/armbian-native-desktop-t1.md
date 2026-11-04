# Armbian 原生桌面 T1（2026-10-30）

实机 r6 RAM 环境启动了官方 Armbian KDE Wayland 桌面，KWin 确认 Mali-G610 / Mesa 硬件渲染。用户确认桌面、触摸和屏幕键盘均正常。用户已授权打包、真实启动和分区测试。

当前平板仍运行 r6，SSH `f8test@192.0.2.227`，桌面是本次 RAM 热启动。尚未刷分区，原生可写根文件系统尚未冷启动验收。原系统只读挂载的备份已完成：5718300000 字节，SHA256 `b1bda6ab3d064fcaca419d8bd609781609e7f8bfe5bd8632f38584588d645dc6`，gzip CRC 与 tar 清单均通过。

打包：`tools/pack-f8-native-desktop-t1.py`，原生根镜像位于 WSL `/var/tmp/f8-pro-armbian/desktop-t1/native-image/`，输出记录在 `outputs/armbian/official-f8-desktop-t1/`。不要在已有部分镜像时重复运行。最终封包由 finalize-f8-desktop-t1.py 应用密码持久化与首次联网权限配置，再 fsck、哈希、ZIP64 逐项校验。desktop-bundle.json 出现前不视为包已就绪。

BOOT 已生成：49425676 字节，SHA256 `3b488ca72b247146d8a8d79fbf1e3481860852fb691707f84fb4abd4606a2c4c`。FIT 四段/内存布局与真实打包 ARM64 blkid UUID 检查通过。注意 blkid 是 CPIO 内独立 sbin/blkid，不是 BusyBox applet；已修正此前离线测试工具调用错误。

顺序收尾进程 finish-f8-desktop-bundles.py：暂时 SIGSTOP 私人回退构建，完成原生包后 finally SIGCONT，再等待回退镜像并导出私有 ZIP。出现异常会恢复被暂停进程。检查 tools/status-f8-desktop-build.py 与对应 session，不能无检查重复启动收尾。私人导出目录 D:\Netdisk\Other\F8-PRO\private-backups\20261030-original-root 已设置非继承 ACL（LIKImk / SYSTEM / Codex 任务账户）。

原生包已完成并逐项验证：`F8_ARMBIAN_NATIVE_DESKTOP_T1.zip`，2644637068 字节，SHA256 `245bb5c1ad5044f3f27fb451c8053c4ebd0ee6bab4777c5e052fcc27689623e4`。根镜像 SHA256 `9fda4aca3978e39a8bc3b185596c7ff824ce66fd50ce9862062e6cc6595eecd4`。已由 verify-f8-desktop-zip.py 在 Windows 本机读取核对，避免 WSL 共享盘瓶颈。desktop-bundle.json 是完成记录，不要再重打包。

RKDevTool v2.84 当前进程已打开，computer-use 文字状态显示“没有发现设备”，没有点击写入或改动配置。截图首次 FrameArrived 超时；重新选择并激活窗口后文字状态读取成功。平板尚未进入 Loader。私人回退根仍由 build-f8-private-rollback.py 构建，PID1439/session76223；此前顺序收尾因主动把验证移交 Windows 已结束，回退进程已恢复。完成后需 export-f8-private-rollback.py 生成 ZIP.part，再由 Windows verify-f8-private-zip.py 完整验证并改为 .zip；PRIVATE-bundle-manifest.json 出现前不视为私人包就绪。

备份：`tools/backup-f8-before-desktop.py`，WSL 私有目录 `/var/tmp/f8-pro-armbian/private-backups/20261030-original-root/`。完成标记 backup.json。`tools/build-f8-private-rollback.py` 从归档构造可刷回的原根 ext4；该镜像是保留文件、所有者与 UUID 的文件级重建，不是逐扇区克隆。私人备份不得放入通用测试包。

固定分区地址（512 字节扇区）：rootfs `0x00078000`，boot `0x00008000`。原分区表不变。r6 依赖 p6 内 SquashFS，因此必须先关机进入 Loader，不能在 r6 正在运行时写 p6。刷回原系统需要匹配的原根镜像与原 BOOT；单独换原 BOOT 不足以回退已替换的 rootfs。

原生桌面首次联网使用 KDE 网络设置，镜像不带 Wi-Fi 密码或 SSH 主机私钥。首次启动生成新的 SSH 身份；USB 日志 F8ADT1 导出 SSHKEY.PUB。`tools/Connect-F8-Desktop.ps1 -Address IP -LogDrive F:` 通过物理日志盘公钥建立独立主机信任，保留现有 r6 的 known_hosts。

原生桌面采用 f8test 自动登录，测试 sudo 免密码；自动锁屏和休眠暂禁用。后续仍需验证充电/PD 策略与采样校准、音频、蓝牙、休眠；桌面正常不代表上述功能全部通过。
