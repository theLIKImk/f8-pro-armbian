# F8 Armbian 2026-11-03 R2 完整发布包

状态：成品ZIP已生成并通过校验。16GiB ROOTFS＋64MiB BOOT，ZIP约4.704GiB；尚未进行这份成品的新刷/冷启动验收。

本机已从Ubuntu resolute/universe安装fcitx5-module-cloudpinyin 5.1.12-1，通过Fcitx5真实D-Bus配置接口启用CloudPinyinEnabled=True、候选位置2、Backend=Baidu、最小拼音长度4。模块加载/配置回读通过；用非敏感测试拼音nihao查询HTTPS服务，200/有效JSON/“你好”候选通过。没有重启桌面或覆盖既有输入法配置，保留屏幕键盘、图标和短振。

云拼音发送拼音到云服务，可在Fcitx5拼音设置关闭。新账户默认配置由tools/install-f8-cloudpinyin-root.py安装到skel；没有复制个人词库、输入历史或代理凭据。

完整构建使用只读实机快照，工作区/var/tmp/f8-pro-armbian/release-20261103-r2，发布目录outputs/armbian/f8-armbian-20261103-r2。复制前排除所有home/root、Wi-Fi/SSH密钥及连接目录、日志/缓存、机器私密状态；离线仅保留首次设置账户f8setup，所有shadow密码字段锁定。SSH使用新生成的公共默认配置且默认不启用，启用时先生成新主机密钥。Wi-Fi系统连接目录为空、netplan仅NetworkManager通用renderer，无预设SSID/PSK。当前平板连接及账户保留，未刷写任何分区。

BOOT取自当前已验证平板boot分区；FIT元数据和四个载荷逐项哈希校验并保留，分区无用间隙及尾部清零，避免带出旧镜像残留。保持现用内核6.1.115/DTB/ramdisk/resource与root UUID，无固件/分区表更改。

流水线：tools/stage-f8-release-current.py（凭据仅stdin/内存）→ configure-f8-release-root.py（F8_RELEASE_DIR指定受保护副本）→ scrub-f8-release-current.py → build-f8-release-current.py。tools/run-f8-release-current.py串行执行并写progress.json/failed.json。首次碰到旧systemctl生成的绝对启用链接，已修正安装器验证并归一化相对链接后重试；不需重新复制或操作平板。

预期成品ZIP包含BOOT、16GiB ROOTFS、manifest、privacy-audit、SHA256和刷入说明。生成后须完成e2fsck、关键文件从实际ext4回读、网络/SSH清理检查和ZIP CRC检查；单独记录首次向导离屏预览。未执行本成品新刷/冷启动，不能声称该项通过。

刷写沿用已知F8 GPT：BOOT 0x00008000、ROOTFS 0x00078000，不刷Loader/uboot/分区表。ROOTFS会覆盖原系统和账户，个人资料需先备份。首次启动按既有向导创建账户/连接Wi-Fi及扩展文件系统；新账户需自行完成磁场校准和当前boot陀螺仪静置校零，个人校准不打包。

已包含传感器中继R2/网页姿态与CoderTools矩阵绘制修正，详armbian-browser-pose-r2.md。电池仍暂缓，多指近距/高频触摸等历史限制不因本次打包而视为修复。

构建进度恢复以WSL工作区progress.json/failed.json及输出bundle.json为准；后台作业工具返回的内存状态可滞后。当前源系统快照约10GiB，完整image完成前不要变更staging内容。

## 最终结果

- 成品：outputs/armbian/f8-armbian-20261103-r2/F8_ARMBIAN_20261103_R2_BOOT_ROOTFS.zip。
- ZIP字节数：5051101732，SHA256：b6a2acc525a31a12df98a00c1d9364f60d29a9a1de02080bb8bfe9bef20212a8。
- BOOT 64MiB，ROOTFS 16GiB；来源实机FIT载荷哈希均通过，非载荷间隙/尾部清零。
- e2fsck只读检查通过；87项文件从实际ext4回读匹配。Wi-Fi连接目录为空、netplan无预设SSID/PSK、SSH主机密钥/用户授权/known_hosts清除，普通旧账户不在passwd，shadow全部锁定，仅保留向导账户。
- 源界面ARM64模拟预览和实机ARM64原生预览均6页通过；原生测试源码与实际image中的first-run.py哈希一致，无账户创建。首次80秒模拟超时已记录，后续240秒上限重试完成，不能将第一次超时当作通过。
- 镜像内sudo实际指向/usr/bin/sudo.ws，sudo和polkit-agent-helper-1均root:root/4755，first-run-apply.py为root:root/755，sudoers语法通过。初次检查误把sudo链接本身的777当权限错误，已按chroot内路径解析后验证真实目标，未改动正确的镜像权限。
- ZIP全内容CRC校验通过，最终ZIP SHA256已写ZIP-SHA256.txt；manifest.json/隐私报告/SHA256SUMS与刷入说明也在ZIP内。checks-summary.json及原生/模拟预览、权限检查结果存于输出目录。
- 额外检查var/snap、var/lib/snapd及opt的小型操作文件，无私钥头匹配。Snap商店认证/设备私密目录已在复制前排除，保留已安装应用版本数据。
- 首次向导和扩容继承已验收实现，但本份完整新包未实际刷入或冷启动；不要把离屏预览等同于新系统启动验收。

完成时没有刷写平板，现有Wi-Fi/SSH和账户继续保留。仅云拼音安装及启用是本次对运行系统的主动更改。下次构建应重新分配受保护工作目录；当前完整bundle.json存在，构建脚本拒绝覆盖完成产物。
