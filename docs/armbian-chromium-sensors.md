> 最新更新（2026-11-03，R2）：已解决浏览器混轴/停后回弹及CoderTools立方体跨界跳动，用户动作验收通过。当前浏览器兼容入口与打包以[浏览器姿态R2](armbian-browser-pose-r2.md)为准；下文为此前实现/定位记录。

> 更新（2026-11-03，R1）：当前已安装标准IIO/会话中继、共享静置校零及自动亮度，浏览器五种API与系统相对方块、自动亮度已验证。下文保留此前定位/F2历史；当前源码、发布钩子和overlay以[传感器中继R1交接](armbian-sensor-relay-r1.md)为准，F2旧归档未改写。

# Chromium网页传感器未接通：定位记录（2026-11-01）

用户在 `https://toolwa.com/sensor-test/` 测试无数据，原生工具可以读取。本轮只读核对、独立临时浏览器测试；没有修改日常Chromium配置、权限、沙箱、驱动或BOOT。

## 实测

- 平板Chromium `151.0.7922.47`，Ubuntu26.04的xtradeb deb，非Snap/Flatpak。当前进程未发现传感器相关显式启用参数。
- MPU6500 `iio:device1` 只有sysfs读取接口，udev属性没有DEVNAME，未生成`/dev/iio:device1`；这是S1无IRQ/无buffer的轮询实现。
- AK8963 `iio:device2` 有DEVNAME `/dev/iio:device2`，原生APP使用每轴`in_magn_[xyz]_scale`和用户校准。
- 普通用户对现有加速度、角速度和磁场raw文件均可读，不能把现象简单归咎于Unix文件权限。
- 已下载用户测试页HTML与脚本供核查。该页面含Generic Sensor与DeviceOrientation/DeviceMotion接口调用，页面要求HTTPS；本轮未读取用户浏览历史、标签页或日常配置文件。

独立测试：普通用户启动默认沙箱、全新临时profile，仅访问临时本机回环HTTP页面。页面为secure context且visible，accelerometer/gyroscope/magnetometer权限均granted；预留6秒真实时间以等待原生枚举：

- Accelerometer/Gyroscope接口存在，但启动都报 `NotReadableError: Could not connect to a sensor`。
- RelativeOrientationSensor/AbsoluteOrientationSensor同样失败。
- `window.Magnetometer` 默认未暴露。

这个权限结果只代表独立测试profile，不冒充用户日常站点的权限状态。测试没有访问远程页面或使用假传感器数据；临时HTTP仅监听127.0.0.1，退出已关闭。初次virtual-time测试未等待足够原生时间，不据其无回调判定结果，采用第二次真实时间测试。

## 与实际版本源码核对

已获取与浏览器版本完全对应的151.0.7922.47源码：`analysis/armbian/browser-sensors/151.0.7922.47/`。

[`SensorDeviceManager::OnDeviceAdded`](https://github.com/chromium/chromium/blob/151.0.7922.47/services/device/generic_sensor/linux/sensor_device_manager.cc)先取udev devnode，空值直接return；因此当前MPU6500被Chromium跳过，尽管它稍后实际通过sysfs轮询，并不通过字符设备读取数据。该backend不使用原生APP/SensorProxy的读取结果。

另外，该版本 [`sensor_data_linux.cc`](https://github.com/chromium/chromium/blob/151.0.7922.47/services/device/generic_sensor/linux/sensor_data_linux.cc)磁场比例只读取共同的`in_magn_scale`，缺失则按1。当前AK8963提供每轴比例，且GUI的校准/安装矩阵为应用层配置；即使后续暴露网页Magnetometer，也不能直接认为数值单位和指南针方向会继承本机APP修正。

网页安全上下文和权限要求可参考[Chromium传感器设计说明](https://www.chromium.org/developers/design-documents/generic-sensor/)及[Chrome传感器文档](https://developer.chrome.com/docs/capabilities/web-apis/generic-sensor)。当前实际浏览器默认不暴露Magnetometer，不能用“磁场驱动能读”直接判定该JavaScript接口可用。

## 状态与后续

**原生六轴/指南针验收保持，浏览器兼容层未完成。** 已定位至少两个独立阻碍：MPU轮询节点被Chromium devnode检查排除、网页Magnetometer接口默认不暴露；另有磁场单位/矩阵/校准继承差异。未部署浏览器修复。

后续应先选择并验证正式兼容路径：Chromium后端支持无字符设备的IIO sysfs节点，或驱动注册真实可用的IIO接口；不得伪造devnode绕过检查。之后再核对网页磁力计暴露和各轴单位/安装矩阵，保留原生自动旋转、触摸、个人校准。仅开启站点权限不能解决已证实的MPU枚举失败；不应为此关闭沙箱或以root运行浏览器。

证据：`local/hardware/browser-sensors-before01.json`、`browser-sensor-api01.json`、`browser-sensor-api02.json`。工具 `tools/read-f8-browser-sensors.sh`、`probe-f8-browser-sensor-api.sh`；本轮无重启、刷机或日常浏览器改动。
