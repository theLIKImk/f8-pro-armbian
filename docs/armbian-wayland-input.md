# Wayland 登录及桌面键盘配置

2026-10-29。仅完成版本化源码、配置与软件包审计，尚无登录或触屏输入实测。

签名 APT 的 SDDM 候选为0.21.0+git20250502.4fe234b-2，依赖Qt6。对应上游GreeterApp.cpp明确在Wayland且InputMethod=qtvirtualkeyboard时清空该输入法设置，因此旧候选不能仅靠Qt6虚拟键盘插件完成Wayland登录键盘。

已修正armbian/candidates/sddm-wayland.conf：DisplayServer=wayland、InputMethod留空，由KWin使用--inputmethod启动/usr/bin/maliit-keyboard；KWIN_IM_SHOW_ALWAYS=1仅放入该greeter合成器命令环境，让键盘不依赖上一次输入设备类型。此设置仍须验证焦点、密码输入、遮挡、隐藏与触摸行为；候选未安装或启用。

桌面候选armbian/candidates/kwinrc使用[Wayland] InputMethod指向com.github.maliit.keyboard.desktop，并启用VirtualKeyboardEnabled。KWin6.3.6的main_wayland.cpp读取该desktop文件中的Exec，inputmethod.cpp支持VirtualKeyboardEnabled及KWIN_IM_SHOW_ALWAYS。没有全局设置QT_IM_MODULE，也没有将登录合成器参数错误套用到每个客户端。Maliit的desktop入口已从实际下载的软件包中核对。

原安装使用--no-install-recommends，未选入SDDM主题，现已在armbian/wayland-packages.txt显式补入sddm-theme-debian-breeze。两个Breeze主题包已独立下载/解包并按签名APT索引SHA256核验，QML包含VirtualKeyboardLoader。主题源码中的按钮/loader存在不代表外部Maliit已显示或输入成功。

重要接续：当前正在运行的APT使用补主题之前的包清单。本次安装结束后，先确认其退出与配置状态，再运行tools/install-f8-wayland-root.sh补主题（已有包由APT处理），不能启动并发APT。旧wayland-packages-installed.ok不自动证明新增主题已装。随后运行tools/verify-f8-wayland-root.py，检查最新完整包清单、ARM64 ELF、Plasma Wayland会话、主题和键盘组件；验证器持有与安装器同一flock，安装尚未完成时拒绝运行。

源码/包校验与候选配置断言由tools/audit-f8-wayland-input.py完成，证据在analysis/armbian/userspace/input-method-audit/audit.json。verify-f8-wayland-root.py已准备，但尚未在完成安装的根目录执行，不能宣称该检查已通过。验证器仅报告构建machine-id/SSH密钥是否需要清理，不输出其内容，也不自动生成可启动镜像。

参考：[SDDM对应源码](https://github.com/sddm/sddm/blob/4fe234b/src/greeter/GreeterApp.cpp)、[KWin6.3.6输入法实现](https://github.com/KDE/kwin/blob/v6.3.6/src/inputmethod.cpp)。这些为上游版本依据，Debian补丁后二进制及实际DRM显示仍需验收。
