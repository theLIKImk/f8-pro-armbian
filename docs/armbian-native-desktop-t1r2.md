# T1r1 原生 KDE 已启动，状态页抢占 VT；T1r2 修复（2026-10-30）

用户现象：见 KDE 启动画面后又显示 F8 RK3588S PAD 字符页。F:55份日志已存 local/hardware/armbian-native-desktop-t1r1-failure-20261030-01/，不可覆盖。目录名称含failure，但本次原生桌面/GPU已取得进展，不代表全部失败。

已验证：SDDM active/running，hardware服务active/exited/success，系统0失败单元；f8test UID1601会话已进入 KDE Wayland。KWINFO.TXT 确认 DRM、OpenGL/EGL、Mesa26.0.3、Mali-G610 MC4 (Panfrost)，原生冷启动硬件渲染已观测到。pbuffer离屏测试仍失败，不用于替代真实KWin结果。

屏幕切回原因：JOURNAL.TXT 20:31:36（板上RTC未联网，非真实日历日期）live-status.py写/dev/tty2报 EIO并退出；Restart=on-failure 使它在20:31:39重启，main()再次chvt2。KWin同秒报Atomic modeset/commit Permission denied，随后用户见VT2状态页。KDE会话并未退出。此前成功RAM热启动脚本显式stop状态服务，冷启动桌面配置遗漏了这个交接动作。

T1r2：保留T1r1全部修复，在SDDM的ExecStartPre停止f8-live-status.service，取消其运行/重启任务，再让SDDM接管屏幕。hardware对status仅Wants，停止status不会停止已成功的hardware服务。账户、Wi-Fi设置、SSH身份、内核/DT/resource不变，不重刷rootfs。

只刷 outputs/armbian/official-f8-desktop-t1r2/BOOT_ONLY_ARMBIAN_NATIVE_DESKTOP_T1R2.img 到 boot 0x00008000（49426564字节，SHA256 283c136d299e47e1b6b119a8c8838f513ce81668dedfd6ff99ab3a75961c2c8b）。根分区不勾选，Loader/Recovery不勾、不擦除Flash。

BOOT在验证原生p6 UUID/marker及T1原脚本哈希后，安装 /etc/systemd/system/sddm.service.d/96-f8-status-handoff.conf（已存在时必须为已知内容）；配置随可写根保存。FIT所有payload校验、真实打包BusyBox init语法及ramdisk内存bank边界通过，T1r2冷启动尚待实测。构建 tools/build-f8-native-desktop-t1r2.py；preflight已保存，勿重跑。

下一步：用户重新进入Loader只刷T1r2 BOOT，重启看桌面是否稳定；稳定后用户连Wi-Fi并提供IP。物理USB日志里的新SSH公钥已保存（T1/T1r1同原生根身份），尚未注册known_hosts；用register-f8-desktop-hostkey.py按物理公钥注册后通过ssh-f8-desktop.py执行verify-f8-native-desktop.sh，之后重启验证持久化。不要沿用旧r6指纹/192.0.2.227在线假设。

当前：平板T1r1、屏幕在F8状态页，Wi-Fi未配置/无IP，暂无SSH连接或后台监控。私人回退包与原生root镜像已完整校验，不重复备份/重刷12GiB根。
