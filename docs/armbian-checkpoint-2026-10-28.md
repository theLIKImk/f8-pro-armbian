# F8-PRO Armbian 额度前接续记录

日期2026-10-28，Asia/Hong_Kong。最新要求：仅Wayland，保留SDDM、登录/桌面自动虚拟键盘、新用户向导和全部硬件功能。

## 真机与保护边界

当前平板仍运行原Arch/5.10.160，最后地址192.0.2.227、alarm密钥登录。迁移阶段仅只读访问真机，没有刷写、重启、休眠、加载新模块、改分区或调压。旧KWin3.4画面通过的历史结论保留。SSH入口见f8-ssh-connection.md。

## 已验证输入及产物

1. 固定源码：Armbian build 98692adee6442f6f221200cf8e6642f9c6a7b740；linux-rockchip 85233a85b67928000afc2e966bab86a8c414f1b4，实际6.1.172。源码审计和哈希在analysis/armbian/source-audit。
2. 原厂设备树、CPU/稳压器、DSI VP2路由、VOP图层、eMMC、热关断、ADC键、保留内存和音频草稿在armbian/dts。根编译包装不是整板启动配置。
3. 最后完整设备树验证269项一致，6条零地址保留区警告与原厂相同，无unexpected_warnings。随后新增声卡扬声器GPIO控制属性及检查，需重跑tools/validate-armbian-peripheral-dt.py。音频、触摸、显示通路等未激活。
4. 基础配置合并成功；CW2015/BQ25890/Panthor为m，MMC/ext4/SquashFS/overlay为y。6个AArch64对象构建成功，analysis/armbian/kernel-config/driver-probe-report.json记录哈希；它们属于6.1.172，不能装入官方6.1.115。
5. 官方APT key完整指纹8CFA83D13EB2181EEF5843E41EB30FAF236099FE，与固定build/config/armbian.key一致。官方26.8.3 image/headers/DTB包均按签名APT SHA256校验。内核实际6.1.115-vendor-rk35xx，Image46561792字节，Panthor模块存在，CW2015/BQ25890未启用。
6. 两个额外.ko已针对官方6.1.115 headers与Module.symvers构建，AArch64、vermagic、版本符号校验通过，位于outputs/armbian/extra-modules-6.1.115。官方headers缺少host工具/完整modules_prepare输入，已用其自带源码重建fixdep/modpost和203项目标类型偏移；没有把6.1.172生成头混入。
7. 独立Debian Trixie ARM64基底foreign/second-stage完成，Release签名有效；Wayland依赖模拟通过（794包，未选kwin-x11）。SDDM/KWin启动候选配置在armbian/candidates，整套桌面尚未安装。X11库等包可能仍为SDDM依赖，不代表原生X11会话目标。
8. 最小systemd/udev/dbus/kmod/Mali固件已安装到隔离root，服务启动被policy-rc.d阻止，proc只读且构建后卸载。官方模块及2个额外模块已只在此root中depmod。
9. outputs/armbian/evaluation-core/rootfs.squashfs：154992640字节，SHA256 5081e7f3fdf51d0e11aa831cf11b84f87bd2e6ddb2e0e5fb8c00de35dbb2085e，Windows/WSL一致。镜像内systemd为ARM64，machine-id为空，无SSH主机私钥；Mali固件274432字节，SHA256 43c3c36b914c031d88ae152fd89019d8f99ad41d9879fb5ab7496ed13f7b378b。只是最小评估基底，不是完整Armbian或可刷整盘镜像。

## 当前后台与下一步

WSL基目录 /var/tmp/f8-pro-armbian。仍在补全源码的命令是git -C /var/tmp/f8-pro-armbian/linux-rockchip-config -c http.version=HTTP/1.1 sparse-checkout disable，本次最后检查PID408、工具session21364。恢复时先查是否完成/失败和.git/index.lock，不能并发修改同一源码工作区。

源码完成后才运行tools/build-f8-evaluation-kernel.sh，输出应为明确-f8-pro-armbian-eval后缀；当前尚未启动Image构建，也没有自定义FIT。该脚本使用Armbian fork基础源码，完整框架patch queue/BSP尚未重现，不能宣称正式发布内核。

早期完整Git下载HTTP2中断；两次归档下载中止/超时，*.part不可使用。官方三包完整下载校验已完成，与这些partial无关。

先重跑最新DT验证，然后继续Image/匹配模块和试启动封装。armbian/initramfs/evaluation-init.sh只是候选：ro,noload挂旧Arch作为镜像容器，校验SquashFS后用RAM overlay启动，必须带systemd.gpt_auto=0；尚未打包/执行，官方6.1.115需额外封装overlay/SquashFS模块，不可假定内建。

## 未完成硬件和功能

触摸：运行gslX680_r8，原内核包含多份GSL实现；GSL3673固件和算法表全匹配仅证明表存在，不能据此改名/上传固件。新驱动GPIO属性/坐标仍不同。陀螺仪原节点未绑定，重复地址注册机制需适配。

显示：路由/图层/PHY及参数只完成静态校验，无新内核亮屏/GPU实测。CPU OPP/loader内存回填、PMIC关机/休眠仍需确认。

音频：原声卡路由已迁移；目标multicodecs从声卡读取spk-con，新增与原codec相同GPIO4_A5，仍禁用待验证。ADC键/热极性已有草稿。

Wi-Fi/蓝牙固件和服务只准备候选overlay；USB-C/BQ充电通知、摄像头ISP/IQ、旋转/传感器、SD卡/接口/休眠及首次账户向导未完成。新用户创建/登录验证前不可删除alarm。

恢复工作时可发送：继续F8-PRO Armbian适配，先读HANDOFF.md和docs/armbian-checkpoint-2026-10-28.md，先核查后台源码补全及最新DT验证，再续编；仅Wayland，保留现有Arch与回退资产。
