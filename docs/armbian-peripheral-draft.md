# F8-PRO 外设设备树草稿与触摸核验

> 最新需求：仅使用 KDE Plasma Wayland；原生 X11 双会话要求已取消。相关旧版本约束与X11验收步骤不再执行。

2026-10-29 更新：已追踪原厂 gslX680_r8 对 gslX680_shuping 的静态分派，选中独立 4851 项固件及 512 个 u32 算法配置，与下文通用 GSL3673 表不同。只读 input ioctl 确认原始坐标 800×1280。参考数据及 AArch64 序列化检查已完成，驱动尚未接入，触摸仍禁用。以 docs/armbian-touch-dispatch.md 为最新依据。


2026-10-28。当前产物用于本机编译检查，尚不具备启动条件。

## 真机驱动证据

通过 tools/probe-armbian-porting-baseline.sh 只读检查 sysfs/proc，结构化记录在 analysis/armbian/live-driver-baseline.json。

- 触摸 4-0040，设备名 gslX680_shuping，驱动 gslX680_r8；内核配置是 CONFIG_TOUCHSCREEN_GSL3673=y，GSLX680_PAD 未启用。后续以 GSL3673 分支为主要比较对象，不能因名字相似便选 PAD 驱动。
- 加速度计位于 I2C3（feab0000），3-0068 绑定 gsensor_mpu6500；罗盘 3-000f 绑定 compass_akm8963。上一轮清单中的 I2C2 是笔误，已修正。
- 陀螺仪 3-0068-1 存在但没有 driver 链接；CONFIG_GYROSCOPE_DEVICE 未启用，input 列表也没有 gyro。这是需要补齐的功能，不能把 DT 节点存在记为可用。
- 电量计/充电分别绑定 cw2015、bq25890-charger；音频 7-0011 实际绑定 ES8323。

## GSL 固件对比

tools/compare-gsl-firmware.py 对锁定 Armbian 6.1 的头文件表按小端 8 字节 fw_data 布局编码，与归档原厂未压缩 Image 做完整字节搜索：

| 候选表 | 大小 | 原厂 Image 比较 |
| --- | --- | --- |
| GSL3673_FW | 4719 项，37752 字节 | 完整匹配，偏移 23604328 |
| gsl_config_data_id_3673 | 512 项，2048 字节 | 完整匹配，偏移 38428808 |
| PAD 分支三份固件表、三份算法配置 | 六份表 | 未找到完整匹配 |

详见 analysis/armbian/gsl-firmware-comparison.json，含表和 Image 的 SHA-256。匹配证明原 Image 包含这些完整表，尚未证明定制驱动运行时实际选择它们；未找到匹配也不能单独证明 PAD 驱动不兼容。

GSL3673 仍有明确接口差异：OF 为 GSL,GSL3673，GPIO 属性为 irq_gpio_number/rst_gpio_number；原厂为 gslX680_shuping、touch-gpio/reset-gpio。其默认 SCREEN_MAX 为 2048×1536，而本机原始触摸范围为 800×1280，物理面板为 1200×1920。尚未验证新驱动触摸算法、坐标变换、IRQ 和休眠恢复，暂不改匹配名或向控制器上传固件。PAD 芯片编号不能直接套到 GSL3673 分支。

## 可审查的代码产物

- armbian/dts/f8-pro-peripherals.dtsi：符号化 GPIO、pinctrl、背光参数、加速度计、罗盘、触摸和 codec 节点。背光完整保留原厂 256 级表和默认值 200，codec 时钟以 I2S0_8CH_MCLKOUT 表示。未实例化尚待处理的重复地址陀螺仪；触摸/背光/codec 保持 disabled。
- armbian/dts/f8-pro-compile-check.dts：仅合并锁定的 rk3588s.dtsi 和上述片段，不引入通用 tablet 文件，不包含完整 PMIC、内存、存储或启动适配。
- tools/fetch-armbian-dt-closure.py：获取锁定 SoC 的递归 include，当前 14 个文件，带哈希。
- tools/validate-armbian-peripheral-dt.py：在 WSL 中使用 cpp/dtc 编译 SoC 对照和草稿，通过 fdtget 与原厂 DTB 比较关键参数。没有操作平板。

验证结果：编译成功；15 项原厂参数读回比对通过；草稿和纯 SoC 对照均为 43 条警告，新增警告 0。上游已有 GPU 双节点、graph 等警告仍保留，不称警告已全部修复。输出和完整日志在 analysis/armbian/dt-validation/，验证清单为 validation.json，DTB 文件名明确带 DO-NOT-FLASH。

这只是引用/参数的构建验证，没有 dt-schema 全面验证、驱动编译、内核启动或实际外设功能验收。

## 下一个关键工作：整板供电与显示

原厂 DT 的 PMIC 路径为 /spi@feb20000/rk806single@0，而上游通用 rk3588s-tablet.dtsi 引入 rk3588s-rk806-dual.dtsi。不能直接沿用该 tablet 文件。面板和摄像头电源都依赖本机单 PMIC 的 DCDC_REG8 等供电链，必须逐一核对轨道、电压、使能 GPIO、启动和休眠状态。

下一阶段先比较目标单 RK806 支持与原厂寄存器/供电定义，迁移 DSI0 面板、电源、背光和 graph；再确定触摸驱动兼容补丁及其编译测试。完成全板设备树、存储与恢复验证之前，不组装刷机包。
