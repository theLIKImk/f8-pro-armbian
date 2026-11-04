# USB接口检查（2026-11-02）

## 初次检查结果（恢复前）

USB未正常初始化，不是已验证正常。仅只读检查，未切换角色/重绑/重启/写寄存器/挂载磁盘。

- boot_id `559fe354-2487-4fb8-9e2b-e35a4de37b5e`，官方6.1.115-vendor-rk35xx，DT USB profile仍u5。
- `f8-usb-otg.service` failed，ExecMainStatus=1；开机6秒绑定等待超时。
- f8_otg_vbus模块存在，但I2C `6-006a` 未绑定，启动日志probe返回-16（EBUSY）。`6-0022` FUSB302延迟探测，Type-C类和USB设备列表为空，无USB存储。udisks2 active，故当前不是文件管理器/挂载服务单独故障。
- 只读读取未绑定的6-006a、SMBus寄存器：03=0x30，07=0x8d，0a=0x75，0b=0x16，14=0x1f。未读有清除副作用的故障寄存器0c，未写任何寄存器。
- 当前03 bit5 OTG_CONFIG=1，07 watchdog field=0。保留源armbian/usb/f8_otg_vbus.c的f8_probe在OTG_CONFIG已为1时明确return -EBUSY，在获取GPIO和注册regulator之前退出。该状态与启动-16一致；**尚未证明是谁/何时打开OTG位**，不能认定GPIO被其他驱动占用或硬件损坏。前一条进度中“资源被占用”只是错误码描述，并非已确认GPIO冲突。
- VBUS regulator未注册会使FUSB302依赖无法满足，继而没有Type-C角色和USB host枚举。当前没有插拔复测，未知端口是否接外设/充电器，不能宣称所有USB功能测试完成。

## 下一步

先确认端口连接状态；若继续修复，先拔空端口并确认外部电源/角色，再审查驱动如何安全接管既有OTG状态及开机顺序。不要直接删保护条件、强制输出VBUS或盲写充电参数。需要接管策略及冷启动/重启和U盘枚举验收。此前U5曾重启后USB2 480Mb/s/U盘读文件通过，不代表本次启动仍正常。

证据：local/hardware/usb-health-20261102-01.json、usb-health-20261102-conflict02.json、usb-health-20261102-guards01.json。工具tools/inspect-f8-usb-health.py、inspect-f8-usb-conflict.py、read-f8-usb-probe-guards.py。

用户上一任务多指跟踪仍未完成，见armbian-multitouch-tracking.md。本轮未修改系统配置、驱动、BOOT或分区。

## 已恢复并经用户验收（最新）

用户明确确认接口全部拔空后，执行 `tools/recover-f8-usb-20261102.py`：核对官方6.1.115/U5/模块hash、两驱动未绑定、无外部输入源、芯片身份与看门狗关闭；只将寄存器03由0x30改成0x10（清OTG_CONFIG bit5），读回核对。07=0x8d、0a=0x75保持不变，未改变充电/升压参数。随后正常bind 6-006a、恢复FUSB302，并restart f8-usb-otg。

- VBUS与FUSB302正常绑定，f8-usb-otg active/exited/success。
- 空口恢复后角色是device/sink，此时没有USB host root hub属于可接受状态。首次恢复脚本最后一条错误断言要求空口已有root hub，导致退出1；实际清位/绑定/服务恢复均已成功。已修脚本只要求Type-C类存在，并将外设枚举放到插盘后的独立验证。不要因首次exit1重复直接I2C操作；驱动绑定后该工具会拒绝直接访问。
- 用户插入U盘后自动切换host/source，VID:PID152d:0583，usb-storage绑定，USB2 480Mb/s，sda约63.87GB，sda1/sda2均识别。
- **用户最终确认“能打开并查看文件”。USB存储访问已恢复。**
- 未改内核/BOOT/固件/分区，未重启、未强制host角色、未格式化磁盘或执行磁盘写入测试。驱动日志历史失败仍保留，不代表最新服务失败。
- 本次为当前启动的运行时恢复，**尚未修复或验证重启后遗留OTG状态的自动接管**。现有开机helper/模块文件未改，不宣称永久修复。后续可在端口空闲时进一步处理启动/关机流程与受保护的接管策略，并冷启动/重启验收。电池适配仍跳过。

新增证据：local/hardware/usb-recovery-20261102-01.json（恢复已成功，尾部旧断言失败）、usb-recovery-20261102-enumeration01.json（插盘后正常枚举）；平板审计 `/var/lib/f8-pro/usb-recovery-20261102/runtime-recovery.json`。用户验收已记录于本节。

最终只读核验 `usb-recovery-20261102-read01.json`：4096字节块读取成功，容量63870857728字节，480Mb/s，systemctl失败单元为空；用户打开后sda1由桌面正常exFAT rw挂载，uid/gid1602。未输出用户文件名/内容、未执行磁盘写入测试；桌面rw挂载不等于整个系统保证磁盘零写入。
