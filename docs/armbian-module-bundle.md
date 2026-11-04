# 自定义内核模块与桌面配套

2026-10-29。本轮产物均为本地评估材料，没有加载模块或部署平板。

6.1.172-f8-pro-armbian-eval 的2279个模块已安装到独立staging并去除调试信息。全部ELF为AArch64、vermagic匹配，depmod -e -E完整符号表检查无输出。CW2015/BQ25890/Panthor分别有37/48/233个版本符号逐项匹配；Panthor的gpu-sched、drm_shmem_helper、drm_exec、drm_gpuvm依赖解析通过。

模块包outputs/armbian/evaluation-kernel/modules-6.1.172-f8-pro-armbian-eval.tar.gz大小26,618,696字节，SHA256 d98a2ad8de3b4343a861a652ada1838150d542c94baebf2a4ac8d2715b190f08，Windows/WSL一致。归档不包含指向构建机的build/source链接。报告analysis/armbian/kernel-build/verified-custom-modules.json，逐模块清单custom-modules-manifest.json。

模块已按逐文件哈希配入rootfs-trixie-wayland并重新depmod/符号校验。该根目录仅保留6.1.172模块树；原6.1.115树移动到/var/tmp/f8-pro-armbian/retained-wayland-official-modules保留，最小评估根目录/已校验SquashFS不变。

当前配套关系：

| 内核 | 用户空间/模块 | initramfs |
| --- | --- | --- |
| 官方6.1.115 | 最小evaluation-core及官方模块/额外2个ko | 已有同ABI候选包 |
| 自定义6.1.172-f8-pro-armbian-eval | 独立Wayland桌面SquashFS及本次2279模块 | 已有同ABI独立候选包，见armbian-custom-evaluation.md |

不可将官方initramfs直接与自定义Image搭配。整板DTB仍是禁用草稿，内屏、GPU、触摸、电池/充电等均没有新内核实测。此模块离线检查不扩大为功能通过。

Wayland根目录Breeze主题已补装，原生X11会话文件以dpkg-divert本地规则改名为plasmax11.desktop.f8-disabled，保留原件，包升级遵守diversion。没有安装kwin-x11。

构建生成的RSA/ECDSA/ED25519主机密钥及公钥已仅从隔离桌面根目录移除，machine-id为空。新增f8-pro-ssh-hostkeys.service，由ssh.service.requires引用，启动SSH前执行ssh-keygen -A；systemd-analyze离线unit检查通过，但服务未执行。RAM-overlay评估每次重启密钥不持久，最终持久身份策略仍待存储设计；没有改动历史客户端私钥、known_hosts或真实平板密钥。
