> 更新（2026-11-03）：本报告为适配前对照。后续融合/倾斜补偿及EM30918光学适配已完成并获用户验收，见[传感器F2交接](armbian-sensors-f2.md)。以下保留原始审计证据。

# 安卓镜像与当前Linux传感器差距审计

2026-11-03。仅对照/记录，没有适配新硬件、刷机、写寄存器、全I2C总线扫描、复位或重绑定驱动。

## 结论

基础运动硬件已适配：MPU6500的加速度/陀螺仪，以及AK8963磁力计，均有当前实机IIO真实读数。主要运动功能差距在**软件融合、统一应用接口及进一步标定**，而非已证实遗漏的另一颗运动芯片。

非运动硬件另发现明确的环境光适配缺口，以及需要核实实物的接近传感器声明。

| 项目 | 原厂Android镜像证据 | 当前Linux结果 |
| --- | --- | --- |
| 加速度 | MPU6500，I2C3 0x68，HAL type1 | 已适配，IIO XYZ/scale，SensorProxy识别，自动旋转用户已验收 |
| 陀螺仪 | 同一MPU6500，HAL type4 | 已适配，IIO角速度XYZ，正方体/会话静置校零用户已验收；未宣称全系统长期标定 |
| 磁场/指南针 | AK8963，I2C3 0x0f，HAL type2 | 已适配，平放指北及用户校准已验收；缺倾斜补偿/统一融合接口 |
| 环境光 | ls_em30918，I2C3 0x24，DT okay，HAL type5，feature XML | 未适配：没有3-0024客户端、光线输入/IIO，SensorProxy HasAmbientLight=false；自动亮度尚缺传感器输入 |
| 接近 | HAL type8和android.hardware.sensor.proximity声明 | Linux无接口、HasProximity=false；镜像未见独立接近DT节点，不能仅据HAL表确认实物有可用接近硬件 |
| 霍尔盖板 | hall-mh248 DT okay，未计入HAL五项 | 已适配合盖熄屏/开盖恢复，用户已验收；非惯性传感器 |

## 尚未提供的Android同类运动功能

安卓框架具备根据基础输入合成虚拟传感器的逻辑。以下是软件功能，不对应六颗额外芯片；本轮没有启动原厂Android执行dumpsys，不能把静态框架实现当成原厂运行时逐项验收。

1. **Gravity重力向量**：连续分离重力。现水平仪使用原始加速度，运动时含线性加速度。
2. **Linear acceleration线性加速度**：扣除重力后的运动加速度，尚无对应共享输出。
3. **Rotation vector旋转矢量**：加速度/角速度/磁场融合的绝对姿态四元数，尚无共享九轴融合。
4. **Game rotation vector游戏旋转矢量**：加速度/角速度融合的相对姿态。现正方体仅陀螺仪积分和会话零偏，不具备加速度约束的完整持续融合。
5. **Geomagnetic rotation vector地磁旋转矢量**：加速度和磁场融合姿态、指南针倾斜补偿，尚无实现。
6. **连续Orientation姿态角**：yaw/pitch/roll共享接口尚缺；屏幕四方向自动旋转已正常，两者不能混为一项。

现iio-sensor-proxy 3.8只公开加速度/倾斜/光线/接近接口，没有Compass接口。本轮误在主接口和Compass子接口查询HasCompass均被DBus拒绝，因此没有将该失败伪装成HasCompass=false；磁场IIO和F8指南针APP仍正常。是否提供QtSensors/浏览器等应用所需接口，需要独立接入；没有传感器融合软件包不能单独证明所有应用不支持，结论同时参考了项目现有APP算法。

进一步标定待办：持久化陀螺仪零偏及温漂验证，罗盘软铁/三轴标定、倾斜补偿与精度量化。现会话校零与平面圆周校准不等于这些项目已完成。

## 没有证据支持的“遗漏”

- HAL没有计步器、步态检测、显著运动、气压计等描述。系统通用libsensor.so包含所有Android标准类型名称，不能据此声称本机有这些硬件/功能。
- 原厂DT另启用mma7660@4c（gs_mma7660，reprobe_en=1），但HAL只有一项加速度描述。它可能是同镜像不同硬件的备选探测节点；未确认本机还装有第二颗加速度计，不列为已证实漏适配。
- 五项HAL均声明fifoMaxEventCount=0，不把FIFO批量采样当作原厂已具备而Linux遗漏的功能。
- HAL minDelay=7000µs仅为描述值；DT accel/gyro轮询配置30ms，Linux MPU采样属性当前50Hz，不能把描述值换算后声称实测142Hz或硬件上限。
- MPU温度当前有读取，但属于芯片温度，不是外部环境温度传感器。

## 证据与可复核方法

原厂镜像：`D:/Netdisk/Other/F8-PRO/update-ANDROID12.img`，2283709002字节。

- `tools/audit-f8-android-sensors.py`只读解析RKFW/RKAF、Android sparse super、LP元数据（验证表SHA256）、逻辑分区ext4；无需完整展开3.26GB super。定向提取36个系统/厂商传感器相关文件，未复制用户数据。
- 设备树直接从当前镜像BOOT重新提取，避免把旧分析目录当成此次输入证据；包含MPU、AK8963、MMA7660、EM30918及霍尔。
- 实际64位HAL：`vendor/lib64/hw/sensors.rk30board.so`。解析Android packed RELA/RELR和LP64 sensor_t（104字节，64位maxDelay/flags），解出五项描述。
- HAL HMI+248指向get_sensors_list。反汇编为返回0xa288数组并mov w0,#5，确认五项确为HAL返回表，而非任意字符串命中。接近flags=3，光线flags=2，其他flags=0；这仍不证明接近硬件实际响应。
- 镜像lib64/libsensorservice.so含上述虚拟传感器实现名称。参考AOSP Android12 r1 SensorService.cpp：accel+gyro可注册重力/线性加速度/游戏旋转矢量；三类输入齐全可注册旋转矢量/方向；accel+mag可注册地磁旋转矢量。此参考并非宣称厂商二进制与该提交完全一致。
- 当前实机：`local/hardware/linux-sensor-audit01.json`和`linux-sensor-audit02.json`。MPU在3-0068由inv-mpu6050-i2c绑定；AK8963在3-000f由ak8975_magn绑定；IIO设备名mpu6500、AK8963、SAR ADC。旧vendor DT节点disabled是避免驱动冲突，不能据此认定传感器未工作；真正启用的是invensense,mpu6500的imu@68，罗盘由已安装服务动态创建I2C客户端。

完整机器可读汇总：`analysis/armbian/android-sensor-audit-20261103/comparison.json`；HAL表、反汇编、DTB哈希和选取文件清单位于同目录。

## 后续优先顺序

若继续适配，先核对/接入EM30918环境光以支持自动亮度；运动侧优先共享六轴/九轴融合与指南针倾斜补偿；接近传感器先核实芯片功能、厂商驱动/安卓实机，再决定是否实现。此次仅登记差距，未启动这些改动，也未加入未经验证的驱动到打包内容。

AOSP参考：[HAL sensor_t ABI](https://android.googlesource.com/platform/hardware/libhardware/+/refs/tags/android-12.0.0_r1/include/hardware/sensors.h)、[虚拟传感器注册逻辑](https://android.googlesource.com/platform/frameworks/native/+/refs/tags/android-12.0.0_r1/services/sensorservice/SensorService.cpp)。
