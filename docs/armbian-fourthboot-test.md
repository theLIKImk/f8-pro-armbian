# R4：RAM overlay 中启动评估 systemd

2026-10-29更新：本候选已真机运行PID1/专用target；系统因resolved 200/CHDIR处于degraded，详见[实测结果](armbian-fourthboot-result.md)。下文为保留的测试前说明。

2026-10-29。原 Arch/5.10.160 SSH 已实际恢复确认。936742912 字节的 Trixie 评估 SquashFS 已新增到 /var/lib/f8-pro/armbian-evaluation/rootfs.squashfs，传输及落盘后重新核验 SHA256 a69fdacdc7ad5fc1d9239ffb271c40bb2e05fb151e0635c2f59b2ef70885a8dc。通过临时文件校验后独占发布，没有覆盖其他文件、boot 或原配置；记录 analysis/armbian/userspace/tablet-rootfs-staging.json。

## 本轮改变

前几轮只是独立诊断 init。R4 要把评估系统的 systemd 真正运行成 PID1，但仅启动 basic.target 与专用评估 target/timer，不启动 SDDM/桌面、SSH 或完整 multi-user 服务。

原 Arch 分区只作 ro,noload 容器，镜像再校验完整 SHA 后只读挂载。overlay upper/work 在 tmpfs /run，配置、machine-id、日志等目标写入均留在RAM。目标仍带匹配6.1.172的模块，保留8核/ttyS2、vendor DVFS黑名单及已测USB2固定设备模式。充电/显示/触摸等未测试功能不在此轮启用。

systemd 启动专用 target 后，timer 延时15秒导出一次只读 RAM FAT 日志盘；失败在部分早期 init 阶段时也会尝试导出 mode=init-failed 日志。若在 PID1 交接或更早阶段失败，可能没有 USB 盘，不能据此推断未进入内核；仍按回退流程恢复。

## 文件和离线验证

outputs/armbian/firstboot-diagnostic-r4/BOOT_ONLY_6.1_DIAGNOSTIC_R4_CANDIDATE.img

42119728 字节，SHA256 6adc48f275c1d42ea84287591e276a761e514b54d78fde232ff8b7bbd5c64b6c。Image未改；DT、initramfs与自定义单元为新版本。DT无新增警告，shell/FAT/cpio/FIT、ARM64 blkid依赖及含12KiB的布局检查通过。

目标单元在独立hardlink验证根目录中通过systemd-analyze verify，未运行PID1。ARM64 BusyBox模拟了四次挂载移动各自失败及全部成功，共5条交接/回退fixture通过；未实际挂载设备。verify仍提示镜像原有SSH hostkey单元的权限过宽/可执行，该单元不由本评估target启动；后续启用正式服务前需规范权限。本轮新注入单元为0644，未修改冻结根镜像。

## 测试步骤

1. 按已验证方法进Loader，仅勾boot，地址0x00008000、大小0x00020000扇区，选择R4。不要改其他分区或擦除。原BOOT备份仍使用 firstboot-diagnostic/CURRENT-BOOT-ROLLBACK-64MiB.img。
2. 启动后保持USB连接，等待约2–3分钟。此次需校验并挂载约937MB镜像，然后启动PID1和定时快照，较前几轮慢。
3. 查看 **F861R4** 日志盘，复制全部文件。RESULT.TXT区分systemd或init-failed；PID1.TXT确认PID1，OSREL.TXT确认Debian/Trixie，MOUNTS.TXT确认/为overlay、容器ro/norecovery、lower为只读SquashFS；TARGET.TXT、SYSSTATE.TXT、FAILED.TXT、JOURNAL.TXT用于判断实际单元状态。
4. 有无日志盘都可按原方法只刷原BOOT回退，确认原系统/SSH和充电恢复。没有桌面或SSH是此轮设计，不是失败判据；原Arch系统和镜像暂存文件保留。

R4尚未刷入或在真机运行PID1，不能称评估用户态已成功。通过后再推进图形/触摸及实际Wayland会话，不把basic target通过当完整桌面验收。
