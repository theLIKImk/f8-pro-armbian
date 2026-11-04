# Armbian Wayland 用户空间评估

> 第四轮接续：SDDM上游在Wayland下禁用qtvirtualkeyboard输入法设置，候选已改由KWin启动Maliit；另补入原计划缺失的Breeze主题包，待当前APT结束后再安装。详见armbian-wayland-input.md。原先Qt6 greeter插件方案为待替换历史，不代表登录键盘通过。

> 2026-10-29 更新：官方 6.1.115 的 initramfs 候选已打包，静态 ARM64 BusyBox、blkid 依赖和精确 ABI 文件系统模块通过离线验证。详见 armbian-checkpoint-2026-10-29.md；整板启动与完整桌面仍未验收。

第二轮：tools/install-f8-wayland-root.sh 已在独立 rootfs-trixie-wayland 实际安装桌面，后台session37801，检查日志/完成标记后再继续；原最小评估根目录与已校验SquashFS保留。显式补入PipeWire、电源管理、网络/蓝牙界面、授权代理、portal、IIO代理和Qt6 Wayland。新依赖模拟拒绝kwin-x11及新增内核/引导加载器包。当前尚未完成全部软件包安装或桌面/键盘实测。

2026-10-28用户明确要求仅Wayland，原生X11双会话约束取消。旧Arch 6.7.5源码与补丁保留作历史，不再用于约束新发行版版本。

Debian Trixie作为首个评估基底：官方仓库提供ARM64 KWin Wayland、Plasma、SDDM、Qt6虚拟键盘、Maliit和Mesa。软件包清单 armbian/wayland-packages.txt；用户空间仍需Armbian BSP/整板集成，不能把Debian基底称为完成的Armbian镜像。

独立rootfs位于WSL /var/tmp/f8-pro-armbian/rootfs-trixie-evaluation。debootstrap验证Release签名并完成foreign及QEMU second-stage，ARM64架构检查通过。没有拷贝Wi-Fi凭据、SSH私钥、旧测试sudoers或Arch keyring服务；也未挂载真实设备分区。

正在用官方签名软件源进行apt依赖模拟，禁用Recommends，不显式安装kwin-x11。出现X11库/XWayland等兼容依赖不代表配置了X11桌面会话。SDDM的Wayland compositor与Qt6 greeter键盘需独立验证，Plasma使用Maliit候选，不给所有客户端全局设置QT_IM_MODULE。

固件：目标Panthor声明arm/mali/arch10.8/mali_csffw.bin，Debian firmware-misc-nonfree文件清单含此路径。候选包已列入清单，仍须通过签名APT下载、文件哈希记录和内核加载实测。

独立rootfs-overlay仅准备了Debian兼容的蓝牙Python3入口/条件服务和NetworkManager preserve MAC配置，尚未激活，蓝牙firmware及helper路径仍待安装与ABI核对。没有复制旧5.10模块加载服务。

候选只读试启动脚本 armbian/initramfs/evaluation-init.sh：现Arch分区仅以ro,noload作为测试镜像容器；检查封装SHA和evaluation标记后挂载SquashFS，并用RAM overlay启动systemd。缺校验/镜像/标记则停留诊断，不回退进入现Arch用户空间。必须禁用systemd GPT自动发现。尚未打包、未执行；包装时需完整校验initramfs工具、loop/overlay/SquashFS内建配置、fstab/generator策略、镜像路径及boot容量。

官方参考：
- https://packages.debian.org/trixie/kwin-wayland
- https://packages.debian.org/trixie/libgl1-mesa-dri
- https://packages.debian.org/trixie/arm64/qt6-virtualkeyboard-plugin
- https://packages.debian.org/trixie/all/firmware-misc-nonfree/filelist

当前阶段尚无KDE会话、登录键盘、GPU或完整Armbian启动验收。
