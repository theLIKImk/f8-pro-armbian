# 原生桌面首次冷启动失败及 BOOT 修复（2026-10-30）

用户刷入 T1 rootfs+BOOT 后见 Create root password 控制台，桌面未出现。53份 F8ADT1 日志已从 F: 收集到 local/hardware/armbian-native-desktop-t1-failure-20261030-01/。

已证明：官方6.1.115内核启动，/dev/mmcblk0p6 直接作为 ext4 **rw** 根，native marker 存在；f8test、SSH主机密钥、sudo准备成功，SSH监听22；wlan0驱动已注册，但未设置Wi-Fi，因此没有IP。Panthor驱动已绑定，DSI-1连接/启用1200x1920。

真正阻塞：f8-desktop-hardware.service 的离屏 gpu-probe 返回 No EGL pbuffer config，在 set -e 下退出1；SDDM Requires 该服务，因dependency失败完全没有启动。屏幕root密码提示是留下的Armbian控制台，不是桌面必须等待设置密码。初始“可能首次初始化阻挡”的猜测已被日志纠正。

修复：只将该离屏诊断改为失败记录后继续，仍要求panthor/panel/touch驱动加载成功；不伪造GPU通过标志。实际KWin硬件渲染、触摸、屏幕键盘仍须新冷启动验证。ROOTFS不重刷。

候选 outputs/armbian/official-f8-desktop-t1r1/BOOT_ONLY_ARMBIAN_NATIVE_DESKTOP_T1R1.img，49426244字节，SHA256 `9cc4a4c992130c0e653e10ed22a2c95ba3e9fc7621a2dd8068d7e42ad09d0729`。只写boot地址0x00008000，不勾rootfs/Loader/Recovery、不擦除Flash。内核/设备树/resource字节不变，FIT哈希、打包脚本语法通过，冷启动尚未实测。

BOOT init在验证原生p6 UUID和marker后，按已知旧/新脚本哈希保护更新桌面helper，保留 desktop-hardware.sh.t1-backup；不覆盖其他版本的脚本。更新会保存在现有原生根分区，账号、SSH主机身份和其他设置保留。旧T1包的原始BOOT存在已知首次冷启动阻塞，后续安装应配此修复BOOT并实测。

生成脚本 tools/build-f8-native-desktop-t1r1.py；原脚本哈希保护校验 tools/verify-f8-desktop-t1r1-guard.py。不重打包12GiB根、不重复备份。现有私人回退ZIP已验证，路径与校验见 RESUME-NATIVE-DESKTOP-T1.md。

下一步：用户重新进入Loader，只刷T1r1 BOOT并重启。桌面出现后手动连Wi-Fi、告知IP；已从物理F:保存 SSHKEY.PUB/HOSTKEY.TXT，可用该公钥建立新系统独立SSH信任，尚未注册。随后 tools/verify-f8-native-desktop.sh + KWin支持信息验证真实硬件渲染与重启持久化。不要沿用旧r6 SSH主机身份，也不要把DRM绑定当作桌面渲染已通过。
