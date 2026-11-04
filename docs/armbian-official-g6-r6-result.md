# G6 r6新启动与采样持久化验收（2026-10-30）

用户确认刷入，已实际SSH核验为新boot_id，并比对运行中的live-power.sh、power-refresh.py、bq-adc-oneshot.py、power-readonly.py、graphics-run五个文件SHA与r6镜像CPIO一致。旧r5的RAM补丁备份目录不存在，未对本次启动重新热修。采样修复已随BOOT持久化。

证据local/hardware/armbian-official-g6-r6-20261030-01/boot-verification.json，包含实际哈希、boot_id、服务、GPU及三个独立采样周期；过渡快照state-05.json保留在此前r5证据目录，此处的新目录为本次权威验收。r6 preflight已标真机/新启动/SSH/采样持久化通过并保留before-hardware副本。

三周期均fresh=true、配置未改，ADC样本年龄0.1969/0.1968/0.1991秒，电流兼容估计200/150/250mA，电池ADC4.224V、CW100%。是有时效验证的芯片估计，不是外部仪表校准的实际电流，更不是USB输入电流。

prepare/network成功，SSH/power/status active/running、0失败单元，GPU硬件像素读回通过。图形初始化成功退出，旧Wayland弹窗服务inactive/success，不自动弹窗。状态页服务运行；用户尚未单独确认版式/闪烁细节，勿由服务状态虚构视觉验收。

当前外部输入标志true；用户刷入后当前接电脑还是充电器未再次明确，不仅凭芯片类型码推断电源身份。核验后不需要再次刷入或补RAM文件。

r6可作为后续**远程诊断测试基线**。这不等于充电管理/USB-C PD/快充/保护策略/长期稳定性已完整适配，charging_validated仍false；标准BQ/CW内核驱动仍禁用。保留原BOOT回退。

镜像outputs/armbian/official-f8-live-g6-r6/BOOT_ONLY_ARMBIAN_26.8.1_LIVE_G6_CANDIDATE.img，50080260字节，SHA839dff537aceda1f8aa7ca0b92f6f31ec2fa1e6d4c8b6026bda029d57e06106d。用户已实际刷入，不再沿用“r6待刷/重启丢RAM修复”的r5旧状态。

SSH仍f8test@192.0.2.227:22，原专用密钥与主机身份，Connect-F8-Live.ps1可连接，测试sudo -n可用。平板既有采集服务持续运行，无宿主机后台监控/自动刷机。
