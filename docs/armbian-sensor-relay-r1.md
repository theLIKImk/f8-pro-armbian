> 最新更新（2026-11-03，R2）：已解决浏览器混轴/停后回弹及CoderTools立方体跨界跳动，用户动作验收通过。当前浏览器兼容入口与打包以[浏览器姿态R2](armbian-browser-pose-r2.md)为准；下文为此前实现/定位记录。

# F8 传感器中继与自动亮度 R1（2026-11-03）

## 当前状态与验收

已实机安装，用户确认系统相对姿态方块“静置稳定，转动角度也基本正确”；新版自动亮度“变化平滑，亮度合适”。20个文件与平板/overlay哈希核对通过，增量包及发布配置完成。未修改BOOT，未重打完整ROOTFS。

本次修正了两个不同问题：Chromium无法枚举原MPU6500节点，以及观察工具旧相对方块的纯陀螺积分漂移。新增独立“启用传感器中继（浏览器／应用）”开关，与“启用自动亮度”分开控制。最后保留用户选择：中继关闭、自动亮度开启、偏好0；测试临时切换后已恢复，后续不要擅自把中继重新开启。

## 用户入口

应用菜单“F8 传感器中继与自动亮度”，/usr/local/bin/f8-sensor-relay。上方分别有中继与自动亮度勾选框，下方亮度偏好 -25至+25个百分点。关闭窗口不停止后台服务；关闭中继停止兼容数据输出，不关闭原硬件、原生自动旋转或独立自动亮度。

网页测试先勾选中继，重新启动“Chromium（相机兼容）”并打开HTTPS测试站，允许传感器权限。该入口现在同时保留相机中继和传感器扩展支持，普通Chromium配置未改，已有浏览器进程未被强制关闭。启动参数对已经运行的同一profile不会追溯生效，需完全退出该兼容浏览器再开。

平放后在“F8 传感器观察 → 交互范例”点“静置校零”，等待成功，再点“方块归零”。零偏由当前登录用户的观察程序和后台中继共用；新启动/新内核boot需重新静置校零，未把私人校准烘焙进镜像。方块参考归零不等于修改磁北；相对Yaw仍不具备绝对航向含义。

## 接口与适用范围

1. 标准IIO中继 f8-sensor-relay：加速度、角速度、校准磁场，生成真实/dev/iio:deviceN、sysfs属性及可用kfifo缓冲；不是伪造devnode。字符设备和输入端仅活动用户获得uaccess，sysfs原始只读属性可供兼容IIO应用使用。缓冲配置遵循Linux IIO权限，根用户已验证完整缓冲，普通应用可使用会话D-Bus接口。
2. 会话D-Bus：服务net.f8.Sensors，路径/net/f8/Sensors，接口net.f8.Sensors1。GetSnapshot()返回JSON；GetSettings()返回配置；SetRelayEnabled(b)、SetAutoBrightness(b)、SetBrightnessBias(d)写用户设置；Sample(s)为不超过5Hz快照信号。
3. /run/user/UID/f8-sensor-relay.json：0600原子快照，关闭观察窗口仍由后台生成。包括SI加速度/角速度、重力/线性加速度、六/九轴/地磁四元数、磁航向、磁预测状态与龄期、原始光照/接近、亮度及有效标记。消费者必须检查online、valid、monotonic龄期；继承F2四元数约定wxyz、板坐标到ENU。关闭中继后快照只保留开关/状态/亮度，不继续提供运动数据。

示例（用户会话终端）：

```sh
gdbus call --session --dest net.f8.Sensors --object-path /net/f8/Sensors --method net.f8.Sensors1.GetSnapshot
gdbus call --session --dest net.f8.Sensors --object-path /net/f8/Sensors --method net.f8.Sensors1.SetRelayEnabled true
gdbus call --session --dest net.f8.Sensors --object-path /net/f8/Sensors --method net.f8.Sensors1.SetAutoBrightness false
```

这是标准IIO加会话数据接口，并非为每个应用自动安装QtSensors/Android HAL插件。原SensorProxy方向服务保留，udev对新中继清除IIO_SENSOR_PROXY_TYPE，防止已经变换到板坐标的中继被二次当作旋转源。光照仍为原始ADC而非lux、接近不是厘米；未向网页AmbientLightSensor伪造lux，也不声称Chromium存在通用网页接近接口。

## 内核中继与Chromium

源码armbian/sensor-relay/f8_sensor_relay.c；构建tools/build-f8-sensor-relay.py，沿用F2实际Image/System.map导出CRC核对方法。固定6.1.115-vendor-rk35xx，所有18项导入CRC通过，不使用强制加载。最终模块SHA256：3b55fbfbb75e4d34866a057244915a74d07d2fdd03eb3e345311f68fa8998090。

原始物理驱动未更换、未重绑。普通用户后台只读MPU6500、AK8963和EM30918，经原有效安装矩阵及个人校准后写/dev/f8-sensor-feed；仅允许一个写入者。帧为9个s32加磁有效标记，单位为微m/s²、微rad/s、微µT。内核只接受定长/有限范围整数，真实缓冲帧9个s32、4字节对齐、s64单调时钟时间戳，共48字节。磁场无效时不推送包含无效磁场的整帧；对应sysfs返回EAGAIN，不能把旧值当新值。

关闭写端立即失效；异常超过1.5秒没有新帧也失效。缓冲历史帧有真实时间戳，读取者仍需判断龄期。内核不做I2C或任何背光、马达、电源写操作。

Linux IIO加速度按Linux重力符号发布，Chromium后端会再取负号，网页得到板坐标加速度；角速度rad/s；磁场IIO共同scale为1e-8 Gauss/count，Chromium转换后为正确µT。校准磁场先映射到板轴，再应用共享180°航向约定；原物理AK每轴scale问题不再被误当作网页单位。

目标发布20Hz（重复最近有效磁场测量），实际轮询受sysfs/I2C及调度限制，不宣称硬件采样提升；磁场实际新测量约2.5Hz。当前udev枚举中中继先于原AK被Chromium选中；网页Magnetometer实测约[-15.67,-32.99,-39.01]µT，与中继尺度相符，而非原厂未校准的数百µT值。不同内核/枚举顺序仍需复验，未假定所有发行版永远相同。

Chromium156同时需要 --enable-features=GenericSensorExtraClasses 与 --enable-blink-features=SensorExtraClasses。只开后者会暴露JS类但后端拒绝连接；现已加入既有/usr/local/bin/f8-chromium-camera，保留原profile、相机LD_PRELOAD、Wayland、默认沙箱和权限机制。独立临时profile/回环secure context真实等待测试：加速度、陀螺仪、磁力计、相对姿态、绝对姿态均26次读数成功。未使用假传感器数据、root浏览器或关闭沙箱；不把该测试当成所有网站/普通profile权限均通过。

实现依据：Chromium156 [IIO后端](https://github.com/chromium/chromium/blob/156.0.8078.73/services/device/generic_sensor/linux/sensor_device_manager.cc)、[额外传感器后端开关](https://github.com/chromium/chromium/blob/156.0.8078.73/services/device/generic_sensor/sensor_provider_impl.cc)、[Linux IIO文档](https://docs.kernel.org/driver-api/iio/core.html)。版本源码已保存analysis/armbian/browser-sensors/156.0.8078.73/。

## 相对姿态修正与共享校零

旧“交互范例”方块直接积分GyroPose，即使六轴融合页正常，旧例子仍会累计漂移。现使用六轴重力互补融合，并以conjugate(reference)*current显示相对初始姿态，显示明确的相对Yaw/Pitch/Roll，方块归零仅重设参考。移除固定透视旋转，避免零位方块在画面里仍因装饰视角呈倾斜。六轴页名称改为“重力姿态（Yaw为相对角）”，明确Pitch/Roll参考重力。

gyro_stabilizer.py只在低角速、加速度稳定并持续至少1.5秒/20样本时抑制静止零偏，不强行把姿态角吸附到0；手动校零先减一次，再估计小残余。低速阈值约0.004rad/s，极慢旋转与噪声难完全区分，属于低速轮询工程估计，不保证精密导航。

用户显式静置校零后保存/run/user/UID/f8-gyro-bias.json，0600，板坐标，绑定boot_id；无效/其他boot文件拒绝。观察页及后台中继共用，磁场/光学校准未被改写。实际共享验证30/30有效且静止，校准加载一致，修正后角速度模长峰值0rad/s，设置测试后恢复。用户确认静置稳定及约90°读数基本正确。未保证未经校零或温漂后仍无累积误差。

## 自动亮度

只通过当前用户PowerDevil BrightnessControl.setBrightnessSilent接口调节，不直接写背光硬件。依据EM30918原始值减个人暗基线，以个人室内参考作相对对数曲线（室内参考约35%），限制12%–90%，偏好可调±25个百分点，3秒时间滤波、约2个百分点迟滞。最终每次最多0.4个百分点、最短0.12秒写间隔，约一个255级硬件背光刻度，避免首版每0.7秒跳2个百分点的台阶感。

手动在KDE改变亮度后暂停自动调节60秒；锁屏、已知合盖、bl_power关闭或读数不可用时避让，不解锁/唤醒屏幕。原系统休眠/合盖机制未改。KDE本机GetSessionIdleTime不支持，因此不声称已实现完整的空闲策略整合。关闭自动亮度保留当前亮度，交还手动控制。用户最终确认“变化平滑，亮度合适”。

## 持久化与发布

- 内核模块/usr/lib/modules/6.1.115-vendor-rk35xx/extra/f8-pro/f8_sensor_relay.ko；root校验助手/usr/libexec/f8-pro/sensor-relay-start.py；f8-sensor-relay-hardware.service加入f8-desktop.target。
- 用户服务/etc/systemd/user/f8-sensor-relay.service，graphical-session.target全局启用，加XDG登录启动入口兜底；同一unit重复start幂等，不绑定likimk或固定UID。
- 配置~/.config/f8-pro/sensor-relay.json；私人磁/光配置及运行期零偏不进入镜像。
- tools/install-f8-sensor-relay-root.py --root <Linux根目录>：校验20文件、权限、目标链接、depmod；临时根重复安装通过。tools/configure-f8-release-root.py在F2安装后调用。
- outputs/armbian/f8-sensor-relay-r1/f8-sensor-relay-r1.tar.gz：增量根文件、驱动/服务/程序、清单和源码；需要已有F2基础和匹配内核，不能当BOOT刷写。SHA256 7d43481c85851d0c1714692997fdefcca3c86eb8c9f385c648a8419bb7d14a5f。
- tools/package-f8-sensor-relay.py生成归档并验证哈希/模式/链接、同步overlay；LF换行已核对，避免首版Windows CRLF导致启动脚本路径带\r的问题。

旧F2归档与验收保留为历史，当前源码/overlay的融合及例子已被R1更新，发布应包含本R1。依赖python3-dbus/python3-gi/python3-pyqt6（实机已有）；armbian/sensor-relay/packages.txt记录依赖。

## 验证、回退与未验范围

数学生成90°、重力/九轴/时间戳回归、静止零偏/运动拒绝/慢转保留、自动亮度曲线/小步/手动覆盖测试均通过；共享校准0600及boot校验测试通过。真实IIO48字节缓冲、浏览器五种API、中继关闭后的原生EAGAIN和D-Bus隐藏运动数据已验证。最终20文件实机哈希及overlay一致，根安装幂等验证通过。

主要证据local/hardware/sensor-relay-browser-extra-final01.json、sensor-relay-final-install02.json、sensor-relay-final-state01.json、sensor-relay-shared-gyro01.json；acceptance.json保存最终验收。用户图形界面验收独立记录，不用离屏结果冒充物理体验。

旧文件备份/var/lib/f8-pro/backups/sensor-relay-r1/；另有F2原程序备份。回退先关闭中继/自动亮度、停止用户服务，卸载f8_sensor_relay，再按备份恢复被覆盖程序和浏览器启动入口，禁用/移除本轮新增启动链接；恢复原F2融合文件时同时恢复其相依版本，不混用新旧模块/用户帧格式。个人磁/光文件不回退覆盖。内核单写入者会拒绝并发feed，退出会立即使数据失效。

尚未验证冷启动、休眠恢复、新用户/新刷完整镜像、各类第三方软件。未进行电池/供电改动，未热重绑摄像头，不恢复已撤回的扬声器曲线。下一次正常重启时顺带检查用户服务、硬件中继和用户开关保持，并重新静置校零即可，不要现在重复要求用户刷BOOT。
