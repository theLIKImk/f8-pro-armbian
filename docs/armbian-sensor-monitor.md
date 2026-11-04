> 最新更新（2026-11-03，R2）：已解决浏览器混轴/停后回弹及CoderTools立方体跨界跳动，用户动作验收通过。当前浏览器兼容入口与打包以[浏览器姿态R2](armbian-browser-pose-r2.md)为准；下文为此前实现/定位记录。

> 更新（2026-11-03，R1）：当前已安装标准IIO/会话中继、共享静置校零及自动亮度，浏览器五种API与系统相对方块、自动亮度已验证。下文保留此前定位/F2历史；当前源码、发布钩子和overlay以[传感器中继R1交接](armbian-sensor-relay-r1.md)为准，F2旧归档未改写。

# F8 传感器观察工具（2026-11-01）

## 2026-11-02：交互范例已加入并通过用户验收

当前入口仍为桌面／菜单“F8 传感器观察”、命令`f8-sensors`。新增默认“交互范例”页，原来的SI读数、原始计数、曲线、服务状态与保存快照保留在“原始数值与曲线”页。用户实际反馈：**“方块和水平仪正常，校零后稳定”**。

| 范例 | 数据与操作 | 边界 |
| --- | --- | --- |
| 陀螺仪正方体 | 真实MPU6500角速度按实际采样时间进行四元数积分，显示XYZ轴和六个面；“方块归零”重置参考，“静置校零”估计会话零偏 | 相对姿态，会漂移，不是绝对朝向／九轴融合；采样间隔过大时跳过积分防突跳；移动时拒绝校零；只保留会话内零偏 |
| 加速度水平仪 | 小球随板体XY加速度移动，显示静态俯仰／横滚和模长 | 动态移动包含线性加速度，不能当作精密姿态角；不修改加速度标定 |
| 磁场指南针 | 读取真实AK8963磁场，复用用户现有指南针校准和已验收layout6/v4方向公式；显示原始磁场模长 | 只在屏幕朝上平放时读航向，没有倾斜补偿；校准缺失或强干扰时提示；v3的Z未校准，不以三轴校正模长冒充绝对场强 |
| 方向与其他状态 | 平板图示跟随SensorProxy；显示真实保护盖、马达输出、MPU芯片温度；可打开现有指南针／霍尔振动测试 | 平放方向未确定时明确标示；温度不是环境温度；不自动启动振动，不强制屏幕旋转 |

范例优先读取udev `ACCEL_MOUNT_MATRIX`（当前已验收矩阵`0,-1,0;-1,0,0;0,0,-1`），回退到有效IIO安装矩阵；只接受正交、行列式+1的旋转，避免把反射当作陀螺仪旋转。原始页仍显示原始芯片轴，快照同时记录范例的矩阵、相对四元数和会话零偏。

MPU目标轮询约20Hz，实际受I2C读取耗时影响；磁场降低到约2.5Hz，方向DBus约1Hz，服务检查约8秒一次。窗口关闭停止读取并释放SensorProxy claim；没有增加开机自启动。QPainter软件绘制，无新增依赖／OpenGL组件。范例页支持触摸滚动，窄窗口可向下看其余卡片。

当前安装：

- `/usr/local/lib/f8-pro/sensor-monitor.py`，SHA256 `c603275cb631105a66f0ed906bc64c94e950c59b459d7a1d5783a028428968b7`。
- `/usr/local/lib/f8-pro/sensor_examples.py`，SHA256 `12d5942e97325e85001a6bdc7c920d3414fc828d139f0d31fb9f9e241e4bf633`。
- `/usr/local/lib/f8-pro/motion_examples_math.py`，SHA256 `39f0aafbda1be7dd2653fa3a3f8bd5f7912b1378c1560fe9e05863184d127e8a`。
- 对应源码均在`armbian/motion/`；原启动脚本与desktop入口未更换。旧单文件备份在`/usr/local/lib/f8-pro/sensor-monitor-before-examples.py`。

验证：`tools/test-f8-sensor-example-math.py`通过已知90°旋转、积分间隔异常跳过、静置偏置估计、移动拒绝、长时间单位四元数与安装矩阵测试。`local/hardware/sensor-examples-smoke02.json`中两个页面实际读取并离屏渲染exit0、约50次样本、无读取错误，温度33.75°C、霍尔打开/马达关闭；截图`sensor-examples-preview02.png`已目视检查，之后仅调整指南针提示换行与方向示意。

`sensor-examples-live04.json`使用真实读数的独立会话完成23组静置校零，偏置约[-0.01713,0.02180,0.01083] rad/s（板体轴），相对四元数归零，读取线程正常退出；此试验对象已销毁，不替代用户当前GUI内的会话校零。初次live03因此前transient窗口unit已不存在而未重启，已改用新unit打开，不能把它记为算法失败。

最终Wayland窗口已打开，用户已物理验证方块／水平仪。磁场范例复用既有校准，本轮没有重新做指北精度验收；现场磁吸附件附近模长较大时有干扰提示，不自动重写个人校准。本轮不改BOOT、驱动、IIO量程/采样率、旋转规则、相机或供电策略。

下方保留最初BT1阶段安装历史，旧“尚无设备”不覆盖当前真实传感器状态。

已按用户要求提前安装到当前原生 KDE，并在 BT1 桌面启动一次。使用系统已有 PyQt6/dbus，无额外下载依赖，无需 root。提供 MPU6500 加速度/角速度 XYZ 原始计数、SI 数值、模长、各100点曲线、SensorProxy方向/识别状态、服务状态，以及手动保存当前快照。

数值显示为传感器原始轴坐标；方向服务使用安装方向矩阵。工具不写驱动配置、GPIO、电源或显示方向，不提供模拟读数。仅在窗口运行时轮询；方向设备存在后通过 SensorProxy claim 获取方向，关闭时释放。没有安装开机自启动。

入口：桌面 `/home/f8test/Desktop/f8-sensors.desktop`，应用菜单“F8 传感器观察”（其他语言环境可能显示 F8 Sensor Monitor），命令 `f8-sensors`。

文件与来源：

- `armbian/motion/sensor-monitor.py` → `/usr/local/lib/f8-pro/sensor-monitor.py`。
- `/usr/local/bin/f8-sensors` 是 Python 启动脚本。
- `armbian/motion/f8-sensors.desktop` → `/usr/local/share/applications/f8-sensors.desktop`。
- 项目安装器 `tools/install-f8-sensor-monitor.py`；安装文件哈希证据 `local/hardware/motion-app/install01.json`。

验证：桌面文件格式校验、普通用户离屏实际运行和PNG渲染通过，预览已视觉检查，无文字截断；普通用户Wayland transient unit `f8-sensor-monitor.service` active。实际预览 `local/hardware/motion-app/install-preview.png`。

安装时仍 BT1 boot `5da89e9f-10f3-4d00-87bf-97df844b1100`，尚无 MPU6500 IIO，界面“等待驱动”正确。没有以此宣称六轴曲线或物理方向通过。S1刷入后打开工具检查真实数据，再协调旋转校准。工具关闭后可随时从桌面重开；不必重建S1 BOOT，其应用和服务配置均保存在原生root。

保存快照按钮默认指向 `~/Documents/F8-sensors/`，用户确认路径后写入当前数据JSON；没有后台自动记录。
