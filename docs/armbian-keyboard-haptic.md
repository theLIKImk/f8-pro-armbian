# Plasma 虚拟键盘按键振动（2026-11-02）

已接入并通过用户实际打字验收：首次旧键盘进程没有振动，经 KDE 重新加载输入法后，用户确认“有短振，手感合适”。当前每次按键请求30ms，保留用户原有按键音、语言及导航设置。本轮未刷BOOT、未重启桌面或平板。

## 实际链路与持久化

当前输入法是 Plasma Keyboard 6.6.6，不是历史记录中的 Maliit。其原生 BreezeKeyPanel 按下处理调用 `org.sigxcpu.Feedback.Haptic.Vibrate`，无需全局监听键盘/触摸，无键入内容记录。

- 官方 Ubuntu 包 `feedbackd`、`feedbackd-common` 0.8.9-1及四项依赖已安装，无升级或移除已有包。D-Bus `/usr/share/dbus-1/services/org.sigxcpu.Feedback.service` 按需启动 `/usr/libexec/feedbackd`；该发行包没有 feedbackd.service，不要误判缺少自启动。
- `/etc/udev/rules.d/70-f8-cover-haptic.rules` 的 F8 Haptic Motor 行新增 `ENV{FEEDBACKD_TYPE}="vibra"`。精确匹配设备名，保留 seat/uaccess 和别名；与发行版72-feedbackd.rules相同标记。仓库副本位于 `armbian/input/70-f8-cover-haptic.rules`，打包须覆盖旧规则。
- 正常用户会话以 FF_RUMBLE 写入 `/dev/input/f8-haptic`，沿用 H2 模块、200ms标称单次保护，不修改GPIO/背光或内核。
- 用户 `~/.config/plasmakeyboardrc` 的 `[General]`：`vibrationEnabled=true`（默认值可能由 KConfig 自动省略），`vibrationMs=30`；原 `enabledLocales=en_US`、`keyboardNavigationEnabled=true`、`soundEnabled=true` 保留。变更前备份 `.config/plasmakeyboardrc.before-f8-haptic`。
- 可在系统设置的虚拟键盘页面关闭按键振动；精确时长可用当前用户执行 `kwriteconfig6 --notify --file plasmakeyboardrc --group General --key vibrationMs 30`。关闭命令同上，将 key/value 改为 `vibrationEnabled false`。GPIO马达为开关控制，时长影响手感，不能宣称支持连续幅度调节。

## 初始化与验证

feedbackd 初次在马达标记前被激活，只导出普通 Feedback 接口。补规则并触发真实设备 change 后，需要结束当前用户旧 feedbackd，再由 D-Bus 正常激活，才导出 Haptic 接口。首轮键盘进程也缓存了旧接口，故仅通过 KWin `/VirtualKeyboard` 的 enabled=false→true重新加载（PID1340→27167），未直接另起脱离KWin的键盘实例。后续正常启动应先模块/udev再登录，冷启动尚未实测。

- 原生接口实测 `Vibrate("org.kde.plasma.keyboard", [(1.0, 30)])` 返回true，10ms观察 `motor_active=1`，130ms观察0。这是GPIO状态采样，不是机械波形精密测量。
- 第二轮用户真实屏幕键盘打字确认短振正常、手感合适；第一轮无振及重载过程如实保留。
- 最终健康快照：同一boot bbeda716-dd1f-4905-a389-62dc09d04c8d，马达空闲0，系统0failed，dmesg无Oops，tainted4608不变。
- 证据 `local/hardware/keyboard-haptic-{feedbackd-install01.json,udev01.txt,native-test02.txt,reload01.txt,final02.json,user-feedback.json}`；操作脚本 `tools/configure-f8-keyboard-haptic.sh`、`activate-f8-keyboard-haptic.sh`、`reload-f8-plasma-keyboard.sh`。

打包rootfs需包含 feedbackd 包及依赖、更新后的70规则、用户键盘配置和已有H2模块/开机加载；仅重打BOOT不能包含本功能。冷启动自动加载及登录后按键反馈恢复仍待后续重启验收。
