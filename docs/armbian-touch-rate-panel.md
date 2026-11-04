# F8 触摸采样率面板（2026-11-03）

已安装“F8 触摸采样率”原生Qt/Wayland程序。用户确认75Hz选择/应用、管理员验证、保留本次设置和恢复原版全部正常。滑块与数值框范围60–120Hz、步进1Hz；全局修改控制器采集时序，不补帧、不仅改变测试App。目标频率是估算请求，不能保证每个整数都精确达到或稳定跟踪。

## 使用

1. 应用菜单打开“F8 触摸采样率”。滑块或数值框选择60–120Hz整数。
2. 点“应用”并完成管理员验证。切换时会卸载/重载触摸模块，触摸可能短暂停顿。
3. 滑动屏幕观察实际中断上报次数、触摸是否跟手。45秒内点“保留本次设置”，否则独立系统timer恢复原版。
4. “恢复原版”可随时返回原始固件/模块。保留只到本次关机/重启；没有修改BOOT或开机默认值。

界面显示目标Hz、实际使用的采集时序参数，以及连续触摸时的实际IRQ计数频率。原版模块没有计数接口，界面标注其历史已测约68Hz，不伪造实时读数。短暂触摸/停手会降低本秒计数，应该持续滑动时观察。

## 频率与时序映射

滑块数字是目标Hz，不是此前“128/122档”的参数数字。表格 `armbian/touch/rate-map.json` 包含61个整数目标，以已测的时序/间隔点分段插值；低于约67.7Hz的部分使用外推。

| 目标Hz | 时序参数 |
| ---: | ---: |
| 60 | 316 |
| 68 | 279 |
| 75 | 252 |
| 90 | 178 |
| 100 | 149 |
| 115 | 127 |
| 120 | 122 |

这些中间目标没有逐档做物理采样率标定。高频参数122虽实测约120.1Hz，但已有明显断触；128约114.5Hz也有77次/20秒触点释放，未通过稳定性验收。面板允许用户试用整个请求范围，提供恢复机制，不把可选择误写为每档稳定。详细硬件试验见 [120Hz调查](armbian-touch-120hz-investigation.md)。

## 模块实现

`tools/build-f8-touch-rate-panel.py` 从保留的原版源生成一个参数化模块，使用现有6.1.115头文件交叉编译，全部导入CRC与实际官方Image核对通过：

- 模块SHA256：`ef95bf30569bd3a5ade8d740cef546c0f01ee5c63c5b1e3a565b4a93e1a8d747`。
- srcversion：`FB0836136B47A05F7029EF6`。
- `period` 参数只在插入时设置，范围122–320，默认280，sysfs只读。
- 固件数组允许在模块初始化时调整0x374，并同步补偿0x180校验word。每次初始化重新验证完整性和为0x5a5a5a5a；校验失败拒绝加载。
- 原触摸跟踪算法及512项配置保持基线。没有将历史T1/T2试验默认写入此模块。
- IRQ入口增加只读 `irq_count`，成功读取包后增加 `read_count`；用于普通用户GUI读取真实计数，不需常驻抓取或tracefs探针。
- 切换以正常rmmod/insmod执行，不强制卸载；原模块完整保留在 `/usr/libexec/f8-pro/f8_gsl_shuping.ko`（SHA bb8fd9db…a505d，srcversion6A8F0920D4E483066E520A4）。

安装的参数模块在 `/usr/libexec/f8-pro/touch-rate-panel/f8_gsl_rate.ko`，不进入系统自动模块目录；只有助手显式载入它。设备休眠/恢复沿用原驱动路径，重载已修正SRAM镜像；整机休眠、冷启动和长期稳定性未在本轮验收。

## 权限与回退

固定助手 `/usr/libexec/f8-pro/touch-rate-control.py` 使用Python隔离模式，经 `org.f8pro.touchrate.control` 的pkexec管理员验证调用。只接受apply 60..120、keep、restore，以及供root timer使用的nonce回退命令；不接收任意模块路径/命令/寄存器地址。

助手检查机型、内核、两份模块SHA、root所有权与非普通用户可写权限；仅管理原版和本面板模块，遇到其他模块版本拒绝覆盖。用全局flock串行化操作，随机token使旧回退任务不会覆盖更新后的设置；“保留”后已经开始但尚未取得锁的旧回调也会被忽略。

每次应用前先保存事务并调度独立45秒timer，再重载模块；GUI退出不取消未确认设置的回退。应用失败尝试恢复原版。状态在root私有 `/var/lib/f8-pro/touch-rate-panel/`，公开 `/run/f8-touch-rate-control.json` 仅含非敏感显示信息。

安装时已串行结束旧122/128手动试用的回退任务并回到原版，避免旧timer影响面板。后续请优先用本面板；旧手动脚本对新模块srcversion的保护检查可能拒绝直接操作，此时先点“恢复原版”。

## 验证与文件

- 映射完整覆盖60–120的61项，period在允许范围内且随目标Hz严格递减。
- 模块编译及实际Image全部导入CRC验证通过。
- 真机75Hz应用映射period252、保留成功；60Hz period316和120Hz period122均成功加载并通过初始化校验。
- 独立回退service通过 `systemctl start --wait` 实际执行，恢复到原版；45秒timer参数核对通过。本轮没有另等完整45秒墙钟到期，因此不把手动触发回调写成“已完整计时等待验证”。
- 59/121越界请求被拒绝，普通用户绕开pkexec直接调用被拒绝。
- 最终恢复原版后打开GUI。用户确认滑块、管理员验证、保留和恢复全部正常。

最终证据 `local/hardware/touch-rate-panel-install02.json`、`touch-rate-panel-verify03.json`。先前verify01的空timer处理错误已修；verify02过早在simple service启动后断言，改为等待服务结束后verify03通过，不能把这些旧文件的失败当当前故障。

源：`armbian/touch/rate-control.py`、`rate-panel.py`、`rate-map.json`、`org.f8pro.touchrate.policy`、`f8-touch-rate.desktop`。工具：`tools/build-f8-touch-rate-panel.py`、`make-f8-touch-rate-map.py`、`prepare-f8-touch-rate-panel-install.py`、`verify-f8-touch-rate-panel.py`。

产物与清单：`outputs/armbian/f8-touch-rate-panel-r1/`；所有运行文件已同步到 `armbian/rootfs-overlay`，未重新生成完整刷机镜像。菜单文件为 `/usr/share/applications/f8-touch-rate.desktop`。回退时通过程序先恢复原版，再移除这组新助手/面板/policy/菜单即可，原BOOT和开机触摸资产均未替换。
