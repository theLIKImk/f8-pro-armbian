# KDE 日期和时间：时区选项卡空白修复

2026-11-03，已安装，用户确认“地图和选择框都正常”。已加入后续发布依赖；未重打整机镜像、未进行冷启动验收。

根因是界面运行依赖遗漏，系统时区数据库和网络同步均正常。日志明确报TimeZone.TimezoneSelector unavailable、module QtLocation is not installed。

本次从Ubuntu源补装qml6-module-qtlocation 6.10.2-1及其依赖；qml6-module-qtpositioning 6.10.2-1原已安装。首次重开页面后又发现缺少地图服务提供者，报QGeoServiceProvider::NotSupportedError；继续补装qt6-location-plugins 6.10.2-1，提供OSM/itemsoverlay插件。地图几何数据/usr/share/timezonefiles/timezones.json由plasma-workspace-data提供，原已存在。

新开的kcmshell6 kcm_clock页面消除了上述模块/地图提供者错误；用户确认地图、地区/城市选择框正常。没有修改当前Asia/Hong_Kong时区或Chrony校时配置，也没有替换KDE二进制/QML源文件。

## 后续打包

- `armbian/kde/timezone-packages.txt`显式列出QtLocation、QtPositioning、Qt Location plugins和plasma-workspace-data，避免no-install-recommends构建遗漏地图插件。
- `tools/install-f8-kde-timezone-root.py --root ROOT --install-packages`安装依赖并检查两个QML模块、OSM插件和时区几何数据。
- `tools/configure-f8-release-root.py`已在创建首次账户前调用安装器；rootfs-overlay保留公开的依赖清单供交接查阅。
- 本次只更新当前系统的软件包和发布流程；没有生成新BOOT/ROOTFS。

## 证据

- `local/hardware/kde-timezone-before01.json`：原QtLocation缺失报错，zone.tab等数据库存在、NTPSynchronized=yes。
- `kde-timezone-deps-start01.json`与`kde-timezone-probe01.json`：APT安装QtLocation成功。临时PyQt QQml探针因未安装PyQt6.QtQml测试绑定而无法运行；没有为探针额外安装绑定，不应将该错误误认为KDE仍缺运行依赖。
- `kde-timezone-open01.json`：页面开始加载，但地图提供者缺失。
- `kde-timezone-map-start01.json`、`kde-timezone-open02.json`：地图插件安装成功，新页面active，日志没有缺失模块/不支持地图提供者错误，仅有上游界面warning。
- 人工验收：用户“地图和选择框都正常”。时区实际修改/管理员认证未额外测试，验证未改变当前时区。

旧的系统设置进程可能缓存先前加载失败的组件；如旧窗口仍空白，关闭该窗口后重新打开即可。
