# R5：修复 RAM overlay 权限并复测服务

2026-10-29更新：本候选已真机通过权限/基础服务检查，系统running且失败单元0。详见[实测结果](armbian-fifthboot-result.md)。以下为保留的测试前说明。

2026-10-29。R4 已真机启动 systemd PID1 和评估 target，但 resolved 因200/CHDIR失败；init的umask077使新建upper目录0700，高概率阻止非root服务遍历根目录。R5明确设upper0755，再挂overlay，保留私有容器/工作目录的保护；注入单元0644、报告目录/程序0755。旧hostkey单元权限只在RAM overlay内改为0644，不修改冻结SquashFS或旧候选。

R5同时将目标hostname设f8-pro-eval，屏蔽apt-daily/apt-daily-upgrade/dpkg-db-backup/fstrim定时器与systemd-pstore服务，减少无关启动活动并保留pstore原证据。不会屏蔽resolved来隐藏其失败。专用target保持原版3单元，其他基本服务按正常依赖启动。

新增PERMS.TXT记录根目录/公共路径与单元权限；NONROOT.TXT运行一次User=nobody的临时服务，读取/etc/os-release并记录退出码；RESOLVED.TXT/DNSLOG.TXT记录服务状态与专用日志；DEVICES.TXT采集DRM/Mali设备、监管数据库文件与模块清单。图形节点仍沿用禁用状态，采集不到DRM/Mali不构成此轮启动失败；它们不代表实际Wayland或GPU验收。

## 候选与离线检查

- 文件：outputs/armbian/firstboot-diagnostic-r5/BOOT_ONLY_6.1_DIAGNOSTIC_R5_CANDIDATE.img
- 大小：42120420字节。
- SHA256：57334c1970a7d17fc31c56ed524f1980c6e13babc2a63a6095f756b81d485d3c。
- Image和原R4冻结rootfs未变，无需重新上传937MB rootfs。
- DT无新增警告，ARM64 shell/blkid、FAT/cpio/FIT四payload、含12KiB扩容的布局预检通过；3个目标单元依赖验证、5条挂载交接回退fixture通过。
- Linux实际降权uid/gid65534的目录访问fixture验证：0700无法读取子文件，0755可读取；未挂真实overlay，不替代R5硬件服务验证。离线clone仍提示lower中旧hostkey单元权限，R5在目标RAM中修正。

## 真机短测

1. 沿用RKDevTool下载镜像操作，只勾boot，起始0x00008000、大小0x00020000扇区，选择上述R5。不要擦除或操作其他分区。
2. 启动后等待2–3分钟，Windows应出现F861R5。无需中途回原Arch重新暂存rootfs；R4已确认暂存镜像可读且哈希匹配。
3. 出现新卷标后通知助手采集。重点验收/权限0755、3单元0644、NONROOT exit_code=0、resolved active且无200/CHDIR、专用target active，检查failed列表与journal。未实测前不承诺所有服务正常。
4. 仍无桌面/网络SSH，充电节点保持禁用。日志保全后可只刷原BOOT恢复使用/充电：outputs/armbian/firstboot-diagnostic/CURRENT-BOOT-ROLLBACK-64MiB.img，67108864字节，SHA256 7e51e71f7ec7439357e5ea2fbb97118715fe5fcf10401b638609df33567b1dd1。

本次仅生成电脑文件，没有写平板、重启或确认R4回退；R5尚未真机运行。下一步依硬件结果进入显示/GPU及触摸启用候选，目标保持KDE Plasma Wayland。
