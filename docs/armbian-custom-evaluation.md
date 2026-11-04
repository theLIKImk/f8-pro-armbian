# 自定义 ABI 的桌面评估封装

目标release为6.1.172-f8-pro-armbian-eval。本轮承接已完成的Image、2279模块与独立Wayland根目录，仍不是可刷整板镜像。

## 本轮实际完成

- 桌面SquashFS：outputs/armbian/evaluation-wayland/rootfs.squashfs，936,742,912字节，SHA256 a69fdacdc7ad5fc1d9239ffb271c40bb2e05fb151e0635c2f59b2ef70885a8dc。离线内容检查通过，Windows/WSL哈希一致。
- 自定义initramfs：outputs/armbian/evaluation-initramfs-custom/initramfs-6.1.172-custom-DO-NOT-BOOT.cpio.gz，2,242,576字节，SHA256 e065e5f114c3920a5648975b3dfe464099fa7a2fd43600ca26e4b8b696c02d91。独立33项newc归档内容、root所有权、设备号、ARM64静态BusyBox及blkid运行依赖检查通过，Windows/WSL哈希一致。没有借入官方6.1.115的ko。
- Image加initramfs为41,714,192字节，小于64MiB boot，但不含DTB/FIT/对齐等，不能据此称刷机包。
- 配套清单outputs/armbian/evaluation-custom-set.json以实际文件哈希绑定四个产物；bootable_board_image=false，hardware_tests_performed=false。报告verified-wayland-squashfs.json与initramfs/custom/verified-initramfs.json记录边界。

打包前曾将mountpoint未挂载返回码误写为1，实际util-linux返回32；已确认proc未挂载并修正判断，重新打包通过。此失败没有影响原系统或旧镜像。

tools/pack-f8-wayland-root.py先核对包/架构/会话和身份状态，再排除proc/sys/dev/run/tmp、var/tmp、日志及APT下载归档生成SquashFS。原官方6.1.115最小镜像不覆盖。新输出目录为outputs/armbian/evaluation-wayland，附DO-NOT-BOOT标记。实际完成与哈希以analysis/armbian/userspace/verified-wayland-squashfs.json为准，文件存在但尚无该报告时不能当完整镜像。

离线内容核对包括空machine-id、无SSH主机私钥、无原生Plasma X11入口、ARM64 systemd/KWin/SDDM、唯一匹配release的2279模块，以及CW2015/BQ25890/Panthor实际内容哈希、Plasma会话、主题和目标SSH生成unit。fstab必须没有实际挂载条目。

tools/pack-f8-evaluation-initramfs.py新增--custom，读取此桌面镜像及其校验报告，核对Image与.config哈希、release、内建文件系统配置。与官方模式分别输出到evaluation-initramfs-custom和analysis/armbian/initramfs/custom，禁止借用6.1.115模块。自定义SquashFS/overlay已内建，不封装对应.ko；文件系统可用性仍由init检查，不忽略模块加载失败。

init按内核已注册文件系统决定是否modprobe，支持官方模块化与自定义内建两种配置；要求内核release与镜像中的modules.dep路径匹配。原Arch容器仍只能ro,noload挂载，PARTUUID、GPT自动发现禁用、镜像SHA和marker检查保留。下层/容器挂载保留于/run，写层为RAM，没有添加写原分区的路径。

FS helper来自桥接助手草案，经主助手复核修改；5条目标ARM64 shell分支测试通过。首次较大桥接请求返回空正文没有采用，见docs/responses-bridge-review.md。这些检查不等于内核启动、挂载、switch_root或实际设备通过。

尚缺整板DT、loader内存修补链及新内核硬件验收，SDDM/KWin候选配置尚未启用，首用户创建与持久状态策略未完成。不能因桌面/模块/归档校验通过就刷写或重启真实平板。
