# F8 网络时间同步修复

2026-11-03，实机已恢复同步；未重启/未冷启动验收。

## 根因与最终配置

系统安装chrony 4.8-2ubuntu1，未安装systemd-timesyncd。内核命令行指定systemd.unit=f8-desktop.target；该目标原本请求不存在的systemd-timesyncd.service，chrony则disabled/inactive，因此timedatectl显示NTP inactive、NTPSynchronized=no。

已启动并启用Chrony，保留Ubuntu默认NTS认证时间源和既有chrony.conf，不添加外部第三方时间源。时区仍为Asia/Hong_Kong，RTC保持UTC。

最终实现不是在目标中硬编码Wants=chrony：已移除旧的systemd-timesyncd和临时直接chrony请求，改用 `/etc/systemd/system/chrony.service.d/50-f8-desktop.conf` 为发行版[Install]追加WantedBy=f8-desktop.target。启用后同时拥有multi-user.target和f8-desktop.target的服务链接，timedatectl启用/停用可按systemd正常机制管理；没有mask其他服务或降低NTS认证。

原目标文件备份：平板 `/var/lib/f8-pro/backups/time-sync-before-r1/f8-desktop.target`。

## 实机验证

- `time-sync-before01.json`：chrony disabled/inactive，时区正确，目标依赖不存在的timesyncd，DNS及默认路由可用。
- `time-sync-fix01.json`：启用Chrony后收到多个有效NTS响应，初始偏差约25秒，等待服务选源校时。
- `time-sync-verify01.json`、`time-sync-verify02.json`：`chronyc waitsync 5 0.1 0 2`成功，`sources`有^*当前选中源和^+其他源，authdata显示NTS，tracking Leap status=Normal；timedatectl显示System clock synchronized: yes、NTP service: active。
- 最终跟踪剩余校正约9ms，这不是绝对精度保证；服务刚启动，频率误差估计仍在收敛。不宣称已完成长时漂移/休眠/冷启动测试。

证据目录 `local/hardware/`；验证未依赖Windows主机时间手动设时。

## 后续打包

- 资产 `armbian/time/50-f8-desktop.conf`，同步至rootfs-overlay同名系统路径。
- 可重复安装器 `tools/install-f8-time-sync-root.py --root ROOT --install-packages`：安装/核对chrony包、修正目标、安装drop-in并创建两个启用链接；仅--root /时执行当前系统daemon-reload和enable --now。
- `tools/configure-f8-release-root.py`已在首次账户家目录创建前调用该安装器；后续发布根目录自动带入本修复。
- 本轮只更新实机、源配置及overlay，没有重新生成完整BOOT/ROOTFS。

如需查看状态：

```sh
timedatectl status
chronyc tracking
chronyc sources
```

本机使用Chrony，因此不要用只面向systemd-timesyncd的timedatectl timesync-status判断Chrony是否工作。
