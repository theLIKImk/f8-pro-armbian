# Fcitx5 中文输入与屏幕键盘 R1

2026-11-03，已安装。用户确认“图标、中文输入和短振都正常”。已接入后续发布流程，尚未重打完整BOOT＋ROOTFS，也未进行冷启动验收。

## 当前配置

- 输入法使用Ubuntu源 Fcitx5 5.1.19-1、中文拼音5.1.12-1，补齐Qt5/Qt6 5.1.13-1、GTK3/GTK4 5.1.6-1前端。
- 默认组为美式英文 `keyboard-us` 与真正的中文拼音 `pinyin`。原先的 `keyboard-cn-altgr-pinyin` 是键盘布局，已从默认组替换。
- Ctrl+空格切换中英文，单独左Shift也可切换。候选词可触摸选择，密码框不启用中文预编辑。
- 原生KDE Wayland通过KWin input-method socket接入；没有全局强制QT_IM_MODULE/GTK_IM_MODULE。新会话设置XMODIFIERS=@im=fcitx和QT_IM_MODULES=wayland;fcitx;ibus，GTK配置提供XWayland接入。
- 当前及新账户的KWin输入法指向 `/usr/share/applications/fyi.fortime.Fcitx5Osk.KwinLauncher.desktop`。
- 当前Ubuntu源未查到fcitx5-osk二进制包；仅配套屏幕键盘采用固定上游源码编译ARM64，其余输入法组件使用APT包。
- 原Plasma屏幕键盘仍保留。菜单“F8 切回原屏幕键盘”可以切回；“F8 中文输入与屏幕键盘”可切回Fcitx5 OSK。SDDM登录键盘没有更换，锁屏功能未单独验收。

## 屏幕键盘及字体

上游：https://github.com/fortime/fcitx5-osk

固定commit：430feb3949b5721df4f37b7c559d52e28951c902，版本0.2.1。构建fcitx5-osk、KWin launcher和modifier helper；未编译实验性KWin二进制插件，未启用HTTP自定义动作。

F8补丁位于 `armbian/fcitx5/patch-osk-haptic.py`：按键通过已有feedbackd非阻塞调用30ms短振，失败不阻塞输入。支持F8_OSK_HAPTICS=0关闭本程序反馈。

modifier helper仅允许Ctrl/Shift/Alt六个修饰键，通过uinput处理上游修饰键兼容问题；同时安装multi-user.target及本机f8-desktop.target启动链接，避免仅标准目标生效。

用户最初看到方框，因为上游默认NotoSerif NF图标字体未安装。现随包提供Symbols Nerd Font 3.4.0及MIT许可证，配置显式加载字体路径并将default_nerd_font设为Symbols Nerd Font。普通中文字使用Noto Sans CJK SC。字体SHA256：71db104aa66567d0efe0b98758f9dfc1895573a453fe85fb53d1c38544a55106。

## 构建与后续打包

源码及默认配置：`armbian/fcitx5/`。软件包清单 `packages.txt`。

1. WSL `rg35xx-build` 运行 `python3 tools/build-f8-fcitx5-osk.py`，复用已有隔离Rust nightly-2026-01-01与AArch64交叉工具链、sysroot。
2. 运行 `python3 tools/package-f8-fcitx5.py`，生成 `outputs/armbian/f8-fcitx5-r1/`。脚本对输出二进制strip，显式记录644/755权限，不使用DrvFS推测权限；压缩包权限和所有文件SHA均已校验。
3. `tools/configure-f8-release-root.py` 在复制setup家目录之前调用 `install-f8-fcitx5-root.py --root ROOT --package outputs/armbian/f8-fcitx5-r1 --install-packages`。安装器核对依赖、文件哈希、权限、动态库和启动链接。
4. `tools/finalize-f8-release-staging.py` 已改为保留新键盘默认配置，并要求根目录存在本组件manifest；不再将其覆盖回Plasma键盘。
5. `etc/skel`包含输入法组、热键、OSK字体、会话环境等默认项。首次开机向导按既有流程复制skel，新账户自动获得配置。rootfs-overlay已同步公开文件；服务启用链接和权限以安装器/manifest为准。

发布包：`outputs/armbian/f8-fcitx5-r1/f8-fcitx5-r1.tar.gz`，12561325字节。
SHA256：b0206977db38b43d723a76dd9ed7b4140febe4ec6314a7a7fbba080398688247。

本次未执行整机镜像重构；不能把源码流程更新当成刷机冷启动验证通过。

## 实机证据及回退

- `local/hardware/fcitx5-deps-check01.json`：APT组件安装成功，KWin tabletMode=true，uinput可加载。
- `fcitx5-install02.json`：启动KWin launcher、Fcitx5、OSK及modifier helper。
- `fcitx5-font-fix01.json`：字体family核对、仅键盘重新加载；输入测试窗口active。
- `fcitx5-verify02.json`：34文件哈希、KWin配置和两条启动链接通过。测试窗口记录原生Wayland预编辑，用户随后关闭窗口；最终缓冲区不含中文，不将其当自动提交通过证据。中文提交与图标/短振结论来自用户确认。实体键盘未另逐项细化记录。
- `outputs/armbian/f8-fcitx5-r1/acceptance.json`：用户反馈、已验及未验项目。
- 当前账户及系统原配置备份位于平板 `/var/lib/f8-pro/backups/fcitx5-before-r1/`（root私有）。

无需管理员权限切回屏幕键盘：

```sh
python3 -I /usr/libexec/f8-pro/switch-keyboard.py plasma
python3 -I /usr/libexec/f8-pro/switch-keyboard.py fcitx5
```

已打开的旧应用可能仍保留旧会话环境；必要时重开该应用。未自动结束用户应用或重启桌面。

## 本轮排错记录

首次编译遇到nightly编译器在渲染warning时内部崩溃，改Cargo --message-format=short后通过，不替换系统工具链。首次传输试验的Base64占位替换损坏数据，被部署前SHA断言拦截，未写系统文件；生成器已改为结构化字面量。打包时发现DrvFS stat会返回777，已改显式权限并添加拒绝组/其他用户可写文件的检查。首次测试窗口用了未安装的PySide6，已切换到现有PyQt6后重开；最终依赖清单已明确包含python3-pyqt6。

参考：[Fcitx Wayland官方配置](https://fcitx-im.org/wiki/Using_Fcitx_5_on_Wayland)、[OSK上游](https://github.com/fortime/fcitx5-osk)、[图标字体及许可证](https://github.com/ryanoasis/nerd-fonts/tree/v3.4.0/patched-fonts/NerdFontsSymbolsOnly)。
