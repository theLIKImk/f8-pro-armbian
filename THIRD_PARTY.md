# 第三方来源与许可

各文件原有版权与许可证声明保持有效；本仓库没有为所有第三方文件统一重新授权。

- Armbian / Linux：使用 Armbian 的 RK35xx vendor 6.1.115 内核；Linux 驱动文件保留各自 SPDX/版权声明。内核与发行版不由本项目原创。上游：https://github.com/armbian/build 。精确整内核构建链仍待锁定，见 BOOT 构建说明。
- Fcitx5 与中文插件：Ubuntu 软件包提供。上游：https://github.com/fcitx/fcitx5 、https://github.com/fcitx/fcitx5-chinese-addons 。
- Fcitx5 OSK：上游 https://github.com/fortime/fcitx5-osk ，固定提交 `430feb3949b5721df4f37b7c559d52e28951c902`；F8 按键反馈补丁在 `armbian/fcitx5/patch-osk-haptic.py`。上游源码可按该提交获取；许可随覆盖层保留于 `armbian/rootfs-overlay/usr/share/licenses/fcitx5-osk/LICENSE`。
- Symbols Nerd Font 3.4.0：https://github.com/ryanoasis/nerd-fonts ，字体许可随覆盖层保留于 `armbian/rootfs-overlay/usr/share/licenses/f8-nerd-fonts-symbols/LICENSE`。
- GSL 触摸参考代码/固件、Rockchip 相机和其他厂商接口依赖：相关来源、参考版本和边界见 `armbian/touch/` 与对应适配文档；保留文件内原始声明。厂商二进制不意味着可由本项目额外授予许可。
- KDE Plasma、Mesa、Chromium、PipeWire 等发行版软件沿用各自的软件包版权与许可证，镜像内保留软件包版权资料。

缺少的构建依赖应从对应上游/发行版获取，不要把第三方二进制误认为本项目可独立重新授权的代码。
