# KDE 中国农历附加日历 R1

2026-11-03。已安装并启用，用户确认“已显示农历”。尚未重打完整镜像或执行冷启动验收。

## 修复

原系统没有plasma-calendar-addons，时钟只启用holidaysevents，因此没有“附加日历（农历）”。已从Ubuntu resolute-updates安装plasma-calendar-addons 4:6.6.6-0ubuntu0.1及kdeplasma-addons-data依赖，含alternatecalendar和astronomicalevents插件。

核对上游6.6.6源码：KSharedConfig文件为plasma_calendar_alternatecalendar，组General，键calendarSystem，值Chinese（注意calendarSystem小写c）。配置dateOffset=0。没有改变系统公历、时区或网络校时。

通过当前用户的PlasmaShell.evaluateScript找到数字时钟，保留原插件列表并追加alternatecalendar，再reloadConfig。实机数字时钟ID19，最终列表holidaysevents、alternatecalendar、astronomicalevents；未清除用户刚选择的天文事件插件，也未重启桌面。

## 后续打包

- `armbian/calendar/packages.txt`：plasma-calendar-addons、qdbus-qt6。
- `tools/install-f8-calendar-root.py --root ROOT --install-packages`：检查附加日历插件和脚本工具，安装公共脚本、KDE自启动及skel农历默认配置。
- `tools/configure-f8-release-root.py`已在复制首次账户家目录之前调用安装器。rootfs-overlay公开文件同步完成。
- `/etc/skel/.config/plasma_calendar_alternatecalendar`默认Chinese。
- `/etc/xdg/autostart/f8-calendar-defaults.desktop`在KDE登录后调用 `/usr/libexec/f8-pro/calendar-defaults.py`，动态寻找当前用户数字时钟，不硬编码部件ID。
- 成功后写用户自己的 `.local/state/f8-pro/lunar-calendar-r1.json`，后续登录不重复覆盖用户选择；没有找到时钟或DBus尚未就绪则短时重试，失败不写成功标志。
- 所有应用、键盘及已修复NTS同步保持原状。

本轮没有复制当前用户的完整桌面布局到发行包，也没有重新生成BOOT/ROOTFS。新账户首次登录效果/冷启动尚未另验收。

## 证据

`local/hardware/calendar-before01.json`：包未安装、原数字时钟插件状态。
`calendar-deps-start01.json`：Ubuntu候选6.6.6及安装任务。
`calendar-plugin-files01.json`：插件/配置QML及安装结果。
`calendar-enable01.json`：实时脚本成功，读取并保留原插件列表，calendarSystem=Chinese。
用户反馈“已显示农历”。

需要重新应用默认项时，可在该用户终端运行：

```sh
python3 -I /usr/libexec/f8-pro/calendar-defaults.py --force
```

一般应通过数字时钟的配置页面调整插件；默认脚本已经执行过后不会反复改回农历。

源码依据：[KDE 6.6.6 alternatecalendar](https://github.com/KDE/kdeplasma-addons/tree/v6.6.6/plasmacalendarplugins/alternatecalendar)。原样源码仅供核对，使用的是Ubuntu提供的二进制插件。
