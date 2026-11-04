# T1r2 启动成功，后续暂缓电池（2026-10-30）

**最新：SSH已验证192.0.2.227，新boot_id/状态页交接/原生rw/KWin硬件渲染/屏幕键盘通过。T1r2已更新实测；首个持久化标记已写，待重启。音频A1 BOOT候选已生成，修复原厂I2S引脚并启用声卡；待用户只刷boot。当前T1r2仍运行，尚未刷A1。详细接续 armbian-native-audio-a1.md；电池继续暂缓。下文未提供IP等旧状态已过时。**

用户明确确认 T1r2 启动成功，并要求继续适配、暂时跳过电池。此前T1r1已观测原生KDE Wayland与Mali-G610/Mesa硬件渲染；本次用户确认状态页不再挡住正常启动。尚待SSH采集T1r2新boot_id、服务状态及交接配置，不能把用户确认替代全部硬件验收。

当前基线：原生可写T1 rootfs，T1r2 BOOT（SHA283c136d299e47e1b6b119a8c8838f513ce81668dedfd6ff99ab3a75961c2c8b）。不重刷rootfs，不重新打包或重复备份。原生SSH主机身份与旧r6不同；从已保存的物理USB日志 SSHKEY.PUB 建立独立信任，不能关闭主机验证。

本轮暂缓电池、电量采样、充电参数和PD策略适配，不改相关寄存器/门限；既有电源服务暂保持原配置。用户尚未提供本次Wi-Fi IP；不要假定旧192.0.2.227在线。已请求用户连接Wi-Fi并提供IPv4。

后续顺序：先采集新系统基线（服务、KWin、输入、屏幕键盘、原生根挂载与持久化），再查音频/扬声器、背光亮度、屏幕方向和蓝牙。摄像头/传感器/休眠随后，具体变更以板级证据和实机只读检查为准。优先远程修补现有原生系统并保存配置，避免重复整包刷机。

已有证据与恢复文件见 RESUME-NATIVE-DESKTOP-T1.md、armbian-native-desktop-t1r2.md；物理公钥 local/hardware/armbian-native-desktop-t1r1-failure-20261030-01/SSHKEY.PUB。下一步注册该公钥后用tools/ssh-f8-desktop.py连接新IP。
