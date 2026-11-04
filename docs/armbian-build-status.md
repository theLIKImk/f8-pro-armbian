# Armbian 构建与ABI接续

> 2026-10-29 更新：完整源码补全成功，自定义 Image 已启动编译；官方 6.1.115 候选 initramfs 离线打包与检查通过。最新状态见 armbian-checkpoint-2026-10-29.md，下文进行中状态为历史。

2026-10-28。用户仅需Wayland。

## 已完成

- 独立Debian Trixie ARM64基底foreign/second-stage完成；Release签名有效。Wayland依赖模拟通过，794个候选依赖，未选kwin-x11，尚未安装整套桌面。
- 固定85233a85基础源码配置合并通过。CW2015/BQ25890/Panthor为m，SquashFS/overlay/eMMC/ext4为y。
- CW2015、BQ25890、RK806 core/pinctrl、RK860、Panthor六个对象交叉编译通过，ELF AArch64。该基础源码实际版本6.1.172，不是官方6.1.115 ABI。
- 官方APT当前key指纹8CFA83D13EB2181EEF5843E41EB30FAF236099FE，与固定构建仓库config/armbian.key一致；隔离rootfs中Signed-By验证元数据通过。旧2019镜像签名指纹不适用于当前仓库。
- 官方26.8.3的image/headers/DTB三包已按签名索引SHA256校验并仅解包。实际内核6.1.115-vendor-rk35xx，Image46561792字节，Panthor=m，CW2015/BQ25890未启用，overlay/SquashFS=m。
- 已用上述精确headers/Module.symvers补编cw2015_battery.ko与bq25890_charger.ko。ARM64、vermagic与版本符号检查通过，待测文件在outputs/armbian/extra-modules-6.1.115/，未加载。

官方headers未提供完整modules_prepare输入及可执行fixdep/modpost。prepare-official-module-tools.py恢复打包配置，仅从自带源码重建host工具；用目标ARM64编译器生成203个devicetable偏移。不能用6.1.172的生成头替代。

## 两条ABI必须分开

- 官方6.1.115配套Image/模块/额外ko：仅可使用同release及符号表。
- 85233a85源码6.1.172：用于F8自定义内建配置和Image构建，计划release后缀-f8-pro-armbian-eval，不混用官方ko。它是Armbian源码基础评估，不表示固定构建框架的完整patch queue和BSP已经重现。

当前F8设备树片段基于85233a85的SoC文件编译验证；不能把该验证自动扩大到6.1.115官方包。官方相近tablet-v11型号名相同但compatible不同，亦不是本机直接可刷DTB。

## 正在推进

完整源码从按需工作区补全，保留所有已编译对象；准备构建带明确后缀的自定义Image。最小评估rootfs正在安装systemd/udev/dbus/kmod及Mali固件，私有只读proc、policy-rc.d阻止服务启动。候选RAM-overlay试启动脚本未打包/运行，现平板系统无更改。

本机WSL基目录/var/tmp/f8-pro-armbian；Windows进度入口TODO/HANDOFF。下一步先读取实际构建日志/marker，不重复启动同一构建。
