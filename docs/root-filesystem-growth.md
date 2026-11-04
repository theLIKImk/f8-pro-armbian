# 正常启动验证与在线扩容（2026-10-28）

正常 boot 真机验证通过：PID1=/usr/lib/systemd/systemd --log-level=info，无 /run/f8diag 或 USB 日志 gadget，system running、0 failed；Wi-Fi 自动连接，机器和 SSH 主机公钥摘要与切换前一致。标准 init 链接已恢复。

## 扩容前检查

- 当前 / 挂载源 /dev/mmcblk0p6、ext4、RW，分区起始 LBA 491520。
- 分区容量 246960619520 字节，PARTUUID 614e0000-0000-4b53-8000-1d28000054a9，与真实 GPT 和既有基线一致。
- 文件系统初始 524288×4096=2 GiB，启用 resize_inode/64bit，预留 GDT 255 块；ext4 errors_count=0。
- 供电 online=1，电池100%。仅为当时扩容条件，不扩展为充电/PD/续航全面验收。

## 备份与执行

先经 SSH 将 /etc、alarm 家目录、板级状态和已有随机种子打包到 WSL 私有 backups 目录。备份包含 Wi-Fi 和 SSH 主机私钥等敏感数据，禁止公开、打印或提交版本控制。验证 gzip 完整性、归档路径以及关键身份/网络文件存在后，记录 SHA-256；Windows `local/backups/pre-root-grow-20261028-config.tar.gz` 副本再次核对摘要。

这是配置/身份备份，配合保留的原始根镜像用于恢复；不是完整运行中文件系统快照，不宣称可以单凭该 tar 恢复任意用户数据。GnuPG S.dirmngr/S.keyboxd socket 在打包时被正常忽略。

随后执行受板型设备约束的 grow-verified-rootfs.sh，所有地址/UUID/容量/电源/错误计数和备份条件再次核对后，在线 resize2fs 到 60293120 个 4 KiB 块。未格式化、未重写根镜像、未修改 GPT 或分区边界。

## 执行结果

- resize2fs 成功，目标 block count 60293120 从实际 superblock 读回确认。
- ext4 错误计数仍为0，物理分区容量未变；机器与 SSH 公钥摘要仍匹配。
- df 显示约227 GiB总空间、951 MiB已用、226 GiB可用。
- systemd running，失败单元0。
- 扩容后的再次重启尚未单独测试；后续重启应检查相同容量和身份，不重新写入旧2GiB根镜像。

工具：prepare-root-space.py、backup-root-config.sh、grow-verified-rootfs.sh。目标 /var/lib/f8-pro/maintenance 下保存前后文件系统头与私有备份摘要标记。WSL /var/tmp/f8-pro-archlinux-20261027/backups 同样保留备份。

脚本保护已完成一次成功执行，备份文件存在会阻止无审查重复；不要为了重跑删除备份或绕过前置条件。
