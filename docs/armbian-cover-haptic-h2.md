# 霍尔保护盖与振动马达 H2（2026-11-02）

**用户已验收：**霍尔开合状态变化正确、能感觉到80ms短振；启用屏幕联动后，再次确认“熄屏和亮屏都正常，没有意外振动”。当前只做合盖熄屏／开盖亮屏，没有启用系统休眠、自动解锁或全局触摸震动。

本轮无需刷BOOT：保留官方6.1.115 Image、C4设备树与原根分区，新增可加载板级输入模块及普通用户桌面服务。boot ID仍`bbeda716-dd1f-4905-a389-62dc09d04c8d`，SSH `f8test@192.0.2.227`。没有改GPU、相机IQ、充电/BQ/PD或CPU策略。

## 原厂接线与实现

| 功能 | 核对结果 | 当前实现 |
| --- | --- | --- |
| 霍尔MH248 | 原厂GPIO0_D3（gpio0偏移27），上拉；原厂hall-active=1的逻辑为低电平合盖 | GPIO双沿IRQ、25ms消抖，标准输入`F8 Hall Cover`，EV_SW/SW_MACHINE_COVER（16）；原始1=打开、0=合上已物理验证 |
| 振动马达 | 原厂GPIO3_C2（gpio3偏移18），高电平使能 | 标准输入`F8 Haptic Motor`，FF_RUMBLE／ff-memless，GPIO二态驱动；不虚构强度等级，默认80ms测试，带200ms标称自动断电保护 |
| 背光 | 实际PWM14_M1为GPIO4_B2（138） | 保持既有正确背光路由；不再使用错误的PWM14_M0/GPIO3_C2作为背光 |

当前DT没有hall/vibrator节点，内核没有OF_OVERLAY且未启用GPIO_VIBRA；原厂hall驱动还依赖Android式电源键／FB状态。采用`armbian/input/f8-cover-haptic.c`单一板级模块，按控制器label及实际父设备核对GPIO，启动输出明确为低，建立自己的GPIO lookup和platform设备，不操作其它设备的绑定。

霍尔用SW_MACHINE_COVER而不是伪造电源键或SW_LID；由专用桌面服务执行屏幕策略，避免直接触发尚未验证的logind休眠。当前GPIO IRQ仍会在DPMS熄屏期间工作；**系统休眠唤醒、登录界面保护盖行为尚未适配/验收**。

## 构建与当前文件

构建`tools/build-f8-cover-haptic.py`，使用现有官方6.1.115头文件、aarch64交叉编译器。全部外部符号CRC与实际官方Image导出核对；`input_ff_create_memless`另与实际发行版ff-memless.ko的导出CRC核对。没有强制加载或跳过版本校验。

- 当前产物`outputs/armbian/f8-cover-haptic-h2/f8-cover-haptic.ko`。
- 安装`/lib/modules/6.1.115-vendor-rk35xx/extra/f8-pro/f8-cover-haptic.ko`，SHA256 `a33e43d75e77ca997527608b2f97ab1971ae04bf7127be3d123e7172a05fcc4c`。
- 源码SHA256 `3460536c1cacd7a971331aad67b8d39e048af958d09bb01e6d440d4f41697032`；vermagic `6.1.115-vendor-rk35xx SMP mod_unload modversions aarch64`。
- `/etc/modules-load.d/f8-cover-haptic.conf`开机加载模块，依赖ff-memless由modprobe处理。
- `/etc/udev/rules.d/70-f8-cover-haptic.rules`只匹配这两个输入设备，提供seat/uaccess及真实设备别名`/dev/input/f8-cover`、`/dev/input/f8-haptic`。规则需在73-seat-late前，不能改回最初99优先级，否则可能错过ACL设置。
- `/usr/local/bin/f8-vibrate`，源码`armbian/input/f8-vibrate.c`，SHA256 `85a73c01b2436a78a0fb8ea9fe3a83fe93dd03871eeb56d2bddc139fe16a8add`。普通用户示例`f8-vibrate --milliseconds 80 --count 1`；先验证设备名、检查忙碌状态，正常参数只允许1–200ms、1–3次。

## KDE屏幕联动与观察APP

- `/usr/local/lib/f8-pro/cover-screen.py` SHA256 `4f7fe8bfddc3e76be590ada14ab371ce714faafefcd48dc8d08c97ee2c1d6105`。
- 用户unit `~/.config/systemd/user/f8-cover-screen.service`已enable，跟随graphical-session.target。
- 用户配置`~/.config/f8-cover.json`当前`validated=true, screen_enabled=true`。读取标准输入事件，调用当前用户Wayland会话的`kscreen-doctor --dpms off/on`；不修改亮度值、屏幕旋转矩阵、休眠策略或锁屏密码。
- 状态`~/.cache/f8-cover/status.json`，含开合状态、事件计数、最近事件及动作错误。使用原子更新；处理SYN_DROPPED时重新查询开关状态。
- 桌面/菜单“F8 霍尔与振动测试”，命令`f8-cover-test`。界面显示开合状态、事件数，提供80ms短振与屏幕联动开关；关闭测试窗口不停止常驻屏幕服务。不自动弹窗，不启用全局键盘/触摸反馈。
- 如需停用屏幕联动，可在测试APP取消勾选；服务停止时尝试恢复屏幕亮起，马达设备关闭／模块卸载／关机时强制关闭输出。

首次观察阶段`validated=false`只收事件，不改变屏幕；物理开合及短振确认后才启用DPMS。用户开合事件closed→open已实录，随后熄屏／亮屏再次人工验收。

## 测试与证据

- `local/hardware/hall-haptic-before01.json`：原输入仅蓝牙电源键、ADC音量键、PMIC电源键和触摸；GPIO27/114空闲。
- `hall-haptic-install02.json`：H2加载成功，保护盖打开时hall_raw=1，motor_active=0。
- `hall-haptic-session-install01.json`、`observer01.json`：普通用户能读霍尔并写FF设备，观察服务和Wayland测试窗口已启动。
- `hall-haptic-policy02.json`：真实closed/open各一事件；保护测试向FF提交1000ms请求，20ms时观察到马达开启、300ms时已关闭，关闭fd后仍为0。表明自动断电在本轮正常工作；不是对实际机械振动波形的精密时长测量。
- `hall-haptic-persist02.json`：系统0 failed、当前dmesg无Oops，tainted=4608与此前一致。
- `hall-haptic-runtime02.json`：最终文件哈希、引脚、GPIO、输入设备及屏幕服务状态。
- `hall-haptic-user-feedback02.json`：两轮用户物理验收。

已写入模块及用户服务自启动配置，**本轮没有重启，冷启动自动加载／登录后策略恢复仍待验证**。后续打包rootfs须包含上述ko、依赖、udev、modules-load、用户服务/配置、脚本和测试入口，不能只重打BOOT。

## H1失败记录

H1产物及module-check保留于`outputs/armbian/f8-cover-haptic-h1/`，不要作为当前版本安装。首次probe返回-524：Rockchip GPIO的gpiod_set_config路径不支持所需上拉。H2改用pinctrl_gpio_set_config设置同一霍尔引脚的原厂上拉，并修正probe错误传播。H1失败后请求资源已释放，没有通电振动、没有留下错误控制器占用。整个过程未热重绑CIF/DPHY/ISP。
