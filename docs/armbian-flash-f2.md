# F8 闪光灯 F2：亮度、常亮与循环闪烁（2026-11-03）

已安装并通过用户实测：常亮、20%至80%的可见亮度变化、循环闪烁、关闭窗口后熄灭均正常。开机加载配置沿用F1，实际模块已升级F2；冷启动尚未验收。未改BOOT、摄像头、振动马达或充电配置。

## 功能与使用

应用菜单仍为“F8 闪光灯”，新增：

- 1–100%亮度滑块，默认25%；单独“立即熄灭”按钮。
- 常亮：控制窗口打开且运行正常时保持。
- 循环闪烁：亮/灭时间分别100–5000ms，默认各500ms；可运行中调整。
- 原半秒短闪功能保留，按当前选择的亮度输出。

原厂仅GPIO3_C1开关控制，F2通过高精度定时器做名义1kHz软件PWM调平均亮度；100%为持续高电平，0为低电平。不宣称硬件PWM、峰值电流调节、光度计校准或相机曝光同步。GPIO为不需睡眠的片上控制器，probe强制检查 `gpiod_cansleep()==false`；否则拒绝启动。GPIO原子上下文要求见 [Linux GPIO consumer文档](https://docs.kernel.org/driver-api/gpio/consumer.html#spinlock-safe-gpio-access)。

## 默认关闭与失联处理

内核标准 LED 为 `/sys/class/leds/f8:white:flash`，max_brightness从1改为100。直接写brightness仍只触发500ms有限脉冲；常亮/循环模式须经固定 `control` 接口显式请求。

界面经pkexec启动固定根权限助手的管道会话，保留已有管理员验证policy。控制命令仅允许off、keepalive、pulse/steady亮度、blink亮度/亮灭间隔，不接受任意文件/引脚或shell。只允许一个会话；第二个实例不影响第一个。

- 界面每秒续期；内核5秒未收到续期就熄灭，不因随后单独keepalive自行重新点亮。
- 正常关闭窗口会发off并关闭管道；助手在EOF或异常退出清理时发off。
- 若界面/助手被强制终止且清理未运行，内核租期仍能熄灭。
- 加载、卸载、关机、休眠均先停止闪烁/PWM定时器并保持低电平；恢复后不自动重亮。休眠/关机路径有实现，本轮未让整机实际休眠或重启验证。

高频GPIO切换只在PWM非零且小于100时运行；灭灯后定时器停止。软件PWM与闪烁时间存在系统调度误差，不能当作硬件同步相机闪光时序。

## 构建与安装

源：`armbian/camera/f8-flash-f2.c`、`flash-panel-f2.py`、`flash-control-f2.py`。F1原始源仍保留，避免覆盖历史结果。

构建命令（WSL rg35xx-build）：

    python3 tools/build-f8-flash.py --revision f2

使用已有6.1.115配套头文件和aarch64交叉工具。vermagic为 `6.1.115-vendor-rk35xx SMP mod_unload modversions aarch64`，全部导入CRC与实际官方Image核对通过。模块SHA256：`56721bbabf8a83291edd0a13703989da298b2bfc864b6f88c0c79e243414b9bd`。

产物 `outputs/armbian/f8-flash-f2/`。通过 `tools/prepare-f8-flash-f2-test.py` 生成只用于当前F1系统的测试payload，先载入实验模块；通过后 `tools/prepare-f8-flash-f2-install.py` 校验F1文件哈希并升级。未使用APT安装/升级软件。

当前路径保持不变：

- `/usr/lib/modules/6.1.115-vendor-rk35xx/extra/f8-pro/f8-flash.ko`。
- `/usr/libexec/f8-pro/flash-control.py`、`flash-panel.py`（内容已为F2）。
- `/etc/modules-load.d/f8-flash.conf`，已depmod并从标准模块路径重载成功，默认off。
- 原policy `org.f8pro.flash.control`；desktop仍为“F8 闪光灯”。

对应rootfs overlay已升级F2，尚未重新打完整刷机包。F1模块/助手/菜单/policy/开机配置的原始副本在平板 `/var/lib/f8-pro/backups/flash-f1/` 下保留原相对路径。恢复时先关闭当前窗口并熄灭，卸载模块，再从该目录恢复这些固定文件、depmod并modprobe；不要只回退助手或模块其中一个，因为max_brightness和控制接口不同。

## 验证结果

内核实机测试通过：

- 25%短闪自动关闭；25%/75%输出状态与PWM边沿计数变化正常。
- 100%持续高电平时PWM计数不再增长。
- 亮200ms/灭300ms循环采样能看到多个亮灭交替。
- off停止PWM；越界亮度/闪烁参数被拒绝。
- 不续期约5秒后自动off；3秒时续期可持续越过最初5秒。
- 正在PWM时卸载，重载后默认off；无新增内核Oops/BUG/WARNING。
- 根权限助手管道EOF后熄灭；第二会话被拒绝且不打断现有会话。
- 用户在图形界面确认亮度变化、常亮、循环闪烁和关窗熄灭四项正常。

证据：`local/hardware/flash-f2-test01.json`、`flash-f2-install01.json`；产物中的 `module-check.json`、`installation-manifest.json`、`acceptance.json`。下次重启需核对F2 max_brightness=100、state为off，才能记录冷启动通过。
