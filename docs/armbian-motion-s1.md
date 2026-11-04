# MPU6500 加速度、陀螺仪与方向适配 S1（2026-11-01）

**最新实机验收覆盖下方待刷状态：S1已启动，boot `62ae5abd-745b-4b3a-85f4-5910371868b0`、192.0.2.227。MPU6500单个IIO已绑定，六轴raw可读，采样重力模长9.853–9.883m/s²，SensorProxy识别加速度计；motion/方向/蓝牙/USB/SDDM active，0failed。用户报告自动旋转已工作但横竖均倒置180°，已部署持久udev矩阵覆盖，用户再次确认“方向和触摸都正常”。无需再刷或重启。陀螺仪仍未完成转动响应/零偏校准；该方向修正尚未做额外重启验证。**

## 180°方向修正与验收

原S1内核矩阵 `0,1,0;1,0,0;0,0,-1` 来自旧厂商layout8，与实际桌面正方向相差180°。已安装 `armbian/motion/99-f8-pro-sensor-mount.rules` 到 `/etc/udev/rules.d/99-f8-pro-sensor-mount.rules`，对本机3-0068的MPU6500设置 `ACCEL_MOUNT_MATRIX=0,-1,0;-1,0,0;0,0,-1`。只翻转屏幕平面X/Y，保留Z轴。

核对了Ubuntu提供的iio-sensor-proxy3.8上游源码 `accel-mount-matrix.c`：有效udev属性优先于sysfs矩阵，因此不改BOOT即可覆盖方向。来源：[Ubuntu官方源码归档](https://ports.ubuntu.com/ubuntu-ports/pool/main/i/iio-sensor-proxy/iio-sensor-proxy_3.8.orig.tar.bz2)。

操作仅reload规则、针对该IIO设备触发change、重启iio-sensor-proxy，属性读回验证通过；未重启桌面、未改原始轴/gyro、供电或显示固定角度。内核sysfs矩阵及观察APP中的安装矩阵仍显示旧值，屏幕方向采用udev覆盖值，这是预期差别。后续root打包必须集成该规则；后续BOOT可将校正矩阵纳入DT，但避免把旧S1矩阵当校准完成。S1镜像哈希未变。

证据：`local/hardware/motion-s1/first-rotation01.json`、`orientation-fix01.json`、`orientation-user-feedback01.json`；root安装前属性与操作结果保存在 `/var/lib/f8-pro/motion-orientation01/`。SSH普通用户运行monitor-sensor时claim被polkit拒绝，此结果不代表本地KDE失败；未放宽polkit，实际桌面旋转与触摸由用户验收通过。gyro读取静止有非零值，尚不宣称校准或转动验证完成。

**观察工具已提前安装：桌面/应用菜单“F8 传感器观察”，当前BT1显示等待驱动正常。提供实时六轴数值、曲线、方向和快照；无需更新S1镜像。详 [观察工具](armbian-sensor-monitor.md)。**

## 当前状态

用户要求适配方向传感器、陀螺仪和加速度计。已完成改前只读基线、原厂接线比对、IIO 模块编译和 ABI 核对、root 服务安装及 BOOT S1 离线打包。**尚未刷入 S1、绑定或读取 MPU6500，没有实机旋转验收。** 当前仍 BT1、boot `5da89e9f-10f3-4d00-87bf-97df844b1100`、SSH `192.0.2.227`。

## 原因与方案

- 原厂 MPU6500 位于 I2C3 0x68，包含加速度与陀螺仪。旧厂商 accel/gyro 共用地址，原系统 gyro 未绑定，不能沿用旧节点即认为可用。
- 当前 I2C3 错用 m0 GPIO1_C0/C1。原厂为 m1 GPIO3_B7/C0（bank3 pin15/16）、400kHz。S1 已按原厂恢复，安装时只读确认新两针与 MPU pinctrl bank3 pin19 无占用。
- 官方 Image 未编译 INV_MPU6050 I2C 驱动。已从本地锁定参考源码 `85233a85b67928000afc2e966bab86a8c414f1b4` 构建未修改的 `inv-mpu6050.ko` 与 `inv-mpu6050-i2c.ko`，单个驱动提供 IIO 加速度及角速度，禁用的旧厂商节点保持禁用。
- 编译头来自 26.8.3，未声称它与实际 26.8.1 Image 相同。每个外部导入 CRC 对照实际 26.8.1 模块或实际 Image 导出表；导出表地址映射交叉核对6201个现有模块符号。报告与模块在 `armbian/motion/official-6.1.115-iio/`。
- 第一版沿用原厂 `irq_enable=0` 的轮询策略，不推测未验收中断线极性，不提供 FIFO/中断缓冲。上游 schema 要求 interrupts；此阶段明确未做完整 schema 验证。
- mount-matrix 初值来自旧 sensor-dev 的 layout8：`0,1,0;1,0,0;0,0,-1`。这不代表物理方向已确认，必须通过四方向旋转校准。
- 保留原厂 MPU enable pinctrl，不添加未经证实的供电控制 GPIO 或 supply 引用；驱动可能报告 dummy regulator，实际芯片响应待确认。不要因失败而盲写电源 GPIO。
- iio-sensor-proxy 3.8 已安装，S1 late-start 服务加载模块、确认两类轴文件存在后启动它。服务不作为桌面启动依赖，不执行显示旋转命令。
- AK8963 罗盘继续 disabled：原厂地址0x0f与常见芯片地址存在差异，尚未确认芯片身份和新驱动匹配。自动屏幕方向由加速度计完成；磁北/指南针方向未包含在S1验收中。

## 已安装 root 资产

`armbian/motion/f8-motion.service` → `/etc/systemd/system/f8-motion.service`，enabled，条件守卫 chosen `f8-motion-trial`。
`armbian/motion/motion-start.py` → `/usr/libexec/f8-pro/motion-start.py`，检查S1 profile和模块哈希，在SDDM/USB/蓝牙启动后加载。
两个模块暂存在 `/usr/libexec/f8-pro/motion/`，未放进depmod搜索路径，避免udev在早期引导自动probe。

安装成功、原系统未加载模块或启动传感器；systemd-analyze verify通过。新服务在BT1回退下条件跳过。安装哈希与证据 `local/hardware/motion-s1/install01.json`，改前快照 `local/hardware/motion-before-20261101.json`。

## BOOT与刷入

文件 `outputs/armbian/official-f8-motion-s1/BOOT_ONLY_ARMBIAN_MOTION_S1.img`，49446208字节，SHA256 `1b39e4e0f49c2085081617f0ef8a1b087886ae3ef6af84330c01f4125dd682c7`。

基于已验收BT1，保留其蓝牙标记及USB U5标记、kernel/ramdisk、CPU cmdline黑名单、音频/背光/触摸；FIT和resource内DT同步。限定DT差异、哈希、内存边界及BOOT容量检查通过。BOOT不包含root服务安装，新root打包需合并runtime-integration资产。

用户安全移除U盘等外设，进入Loader后仅刷boot，LBA `0x00008000`；不刷rootfs/Loader、不擦除。回退使用已验证BT1：`outputs/armbian/official-f8-bluetooth-bt1/BOOT_ONLY_ARMBIAN_BLUETOOTH_BT1.img`。

## 启动后验收

先通过固定公钥SSH运行 `tools/read-f8-motion-s1.sh`，新样本保存到 `local/hardware/motion-s1/`，检查新boot、服务、芯片绑定及六轴读数、比例、IIO方向矩阵、SensorProxy和KScreen。若probe失败，先取dmesg和service日志，不重复加载/复位芯片或全总线扫描。

随后协调用户保持正向竖屏、左横屏、右横屏、倒竖屏，采样并校正方向；确认平放重力模长、静止角速度与转动响应，再验证KDE自动旋转和各方向触摸、屏幕键盘。不要仅以有节点或服务active标记完成。中断缓冲、指南针和休眠恢复留待独立验收；充电参数/PD与调频黑名单不改。
