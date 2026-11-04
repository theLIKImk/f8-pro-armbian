# F8-PRO KDE 电池组件接入（2026-11-01）

## 结果

用户验收：Plasma 托盘出现电池图标，显示 93%。UPower 完整识别 `battery_cw2015_battery`。

## 背景

powerdevil、UPower、`org.kde.plasma.battery` applet（C++ 插件在 powerdevil 包中）本已安装，托盘配置也早已包含 `org.kde.plasma.battery`。此前不显示的唯一原因：系统没有任何 battery 设备（`/sys/class/power_supply` 只有 USB PD 的 `tcpm-source-psy-6-0022`）。

结论：**这不是"装组件"问题，是"电池设备未暴露"问题。**

## 根因

CW2015 电量计（I2C6 总线、地址 0x62）：

- vendor 6.1.115 内核未编译 `CONFIG_BATTERY_CW2015`（/boot/config 确认）
- 运行 DT 无 cw2015 节点（i2c6 下只有 es8388 等运行时绑定设备）
- 芯片本身活着：`i2cdetect -y -r 6` 在 0x62 有响应，寄存器可读（0x00=0x73、0x03=0x6d）

## 修复（不动 BOOT，无需刷机）

1. **模块部署**：使用 2026-10-28 已编译产物
   `/var/tmp/f8-pro-armbian/extra-modules-6.1.115/cw2015_battery.ko`
   （vermagic `6.1.115-vendor-rk35xx SMP mod_unload modversions aarch64` 匹配）
   部署到设备 `/lib/modules/6.1.115-vendor-rk35xx/updates/cw2015_battery.ko` + `depmod -a`

2. **设备绑定（临时验证）**：
   ```
   echo cw2015 0x62 > /sys/bus/i2c/devices/i2c-6/new_device
   ```
   probe 后 `/sys/class/power_supply/cw2015-battery` 出现：capacity 93、Li-ion、Discharging、present 1。

3. **持久化**：
   - `/etc/modules-load.d/f8-cw2015.conf`：`cw2015_battery`（开机加载）
   - `f8-battery-cw2015.service`（oneshot，enabled）：开机执行 new_device 绑定
   - 与现有 `f8-usb-otg` 服务同模式；将来 BOOT DT 加入正式 cw2015 节点后此服务自然多余（无害保留即可）

## 踩坑记录

- `new_device` 的地址必须写 **十六进制 `0x62`**；写 `6-0062`（设备名格式）会报 `Extra parameters`（EINVAL）。
- 驱动匹配名：`i2c_driver.name = "cw2015-battery"`，id_table `cw2015`，of_match `cellwise,cw2015`。new_device 用 id_table 名即可。
- probe 后 dmesg 报 `Failed to get supply state: -19`（ENODEV）：驱动需要 `vdd-supply` regulator，DT 无节点故缺失。**不影响**容量/状态读数，仅电压/温度等可选通道受限。

## 已知限制

- 充电电流/充电器状态未接入：BQ25890 充电管理按用户 2026-10-28 指示继续暂缓。当前"Discharging"读数不代表不能充电（充电硬件电路独立），仅充电软件状态未读。后续开启充电验收时一并处理。
- 重启持久化：服务模式与已验证的 f8-usb-otg 相同，机制上无风险，但尚未实测一次重启确认（可选）。

## 修改文件清单（设备上）

- `/lib/modules/6.1.115-vendor-rk35xx/updates/cw2015_battery.ko`（新）
- `/etc/modules-load.d/f8-cw2015.conf`（新）
- `/usr/lib/systemd/system/f8-battery-cw2015.service`（新，enabled）

## 相关工具脚本（本地 tools/）

- inspect-f8-battery*.sh / find-f8-battery*.sh — 组件与包归属排查
- inspect-f8-cw2015.sh / scan-f8-i2c6.sh / probe-f8-cw2015.sh — I2C 探测
- deploy-f8-cw2015.sh / insmod-f8-cw.sh / bind-f8-cw*.sh — 部署与绑定
- persist-f8-battery.sh — 持久化
- check-f8-bat-sysfs.sh / check-f8-bat-ui.sh — 验收
