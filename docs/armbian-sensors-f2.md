> 更新（2026-11-03，R1）：当前已安装标准IIO/会话中继、共享静置校零及自动亮度，浏览器五种API与系统相对方块、自动亮度已验证。下文保留此前定位/F2历史；当前源码、发布钩子和overlay以[传感器中继R1交接](armbian-sensor-relay-r1.md)为准，F2旧归档未改写。

# F8 传感器 F2 交接（2026-11-03）

## 当前结论

本轮已安装并通过实机和用户验收，无需再次要求用户重复校准/动作测试。最终用户回复：“不再闪烁，方向也正确”；此前确认“跟随正常，静止值较小”和“低光变化可见，远近正常切换”。未改 BOOT，未重打完整 ROOTFS 镜像。

- 传感器观察新增“融合与派生传感器”：六轴、九轴、地磁姿态模式，四元数/欧拉角、重力与线性加速度；保留原交互范例和原始数据页。
- 指南针统一增加 180°，独立指南针与观察界面共享计算；三轴校准支持倾斜补偿。用户确认方向符合要求，未另作手机对照精度验收。
- EM30918 环境光及接近传感器已接入 IIO，观察界面显示原始 ADC、低光增强显示及近/远状态。
- 本轮文件已加入 rootfs-overlay、发布根配置钩子和独立增量包；个人磁场/光学校准不进入发布包。

## 程序与数学

源码位于 armbian/motion/：sensor_fusion.py、fusion_view.py、sensor-monitor.py、sensor_examples.py、motion_examples_math.py、compass-view.py。板坐标姿态到 ENU，四元数顺序 wxyz；六轴采用陀螺积分和重力互补修正，分离重力及线性加速度。九轴使用有效三轴磁场校准作航向修正；地磁模式直接由加速度和校准磁场求解。平面校准不能冒充完整三轴校准。

独立指南针入口 f8-compass --three-axis 明确选择三轴模式，窗口标题“F8 指南针 · 三轴校准”。先前入口默认平面模式的问题已修复。现有个人校准确认 version2、84组、场半径约41.08346µT、RMS约1.54974µT；这是硬铁球面校准，未实现软铁椭球、磁偏角或真北精度保证。

九轴闪烁原因是顺序 sysfs 读取中磁场时间戳略晚于 IMU，旧逻辑将负龄期判失效。现容忍 -0.25秒的有限时序偏差；真实磁场短缺读最多1.2秒陀螺预测，明确标示预测状态，超时失效；移除校准立即失效。20秒100次检查全部绝对姿态有效、0预测帧，最大参考龄期0.399秒。用户最终确认不再闪烁。

共享输出 /run/user/UID/f8-sensor-fusion.json 为观察程序运行期间按需生成的0600原子JSON（不超过5Hz），含有效性、姿态、重力/线加速度、磁预测/参考龄期和光学数据。暂停/退出标为失效；崩溃可能遗留文件，消费者必须检查单调时钟时间戳及有效标记。不是常驻传感器服务，也未注册全系统 Android HAL、QtSensors 或浏览器传感器接口。

## 环境光与接近

实物 EM30918，I2C3@0x24，PID寄存器0x00=0x31。单寄存器读取有效；不能使用此前返回全FF的连续读取结果。配置从原BF改为86，采用已知低驱动15mA/100ms接近模式及普通ALS模式，未猜测提高增益、写复位寄存器或改GPIO/IRQ。模块名称 f8_em30918，IIO名 f8-em30918，环境光 in_intensity_raw、接近 proximity_raw，均为原始计数，不是 lux 或厘米。

用户配合遮光/室内记录：遮光ALS3、室内ALS12；接近远1、遮挡近约209。个人 ~/.config/f8-pro/optical-calibration.json 保存基线/参考，界面采用 log1p 低光显示增强，原始值保留；远近采用35%/65%滞回。没有把遮光当作硬件复位或自动亮度校准。未接入系统自动亮度。

内核模块源码 armbian/motion/f8_em30918.c；构建 tools/build-f8-em30918.py，WSL rg35xx-build。使用官方6.1.115-vendor-rk35xx头文件及实际Image/System.map核对全部12项导入CRC，非强制加载。产物 outputs/armbian/f8-em30918-r1/，module-check.json 保存核对信息。

安装模块 /usr/lib/modules/6.1.115-vendor-rk35xx/extra/f8-pro/f8_em30918.ko，SHA256 e5d684e20f6590583c23ad219d31c9dd964251c6fd5c7b1244cdc8996e092b4d。optical-start.py 校验内核、MPU节点、模块哈希并锁定固定地址，拒绝抢占其他驱动；f8-optical.service 在 f8-motion.service 后运行，启用于 f8-desktop.target，目前active/enabled。

## 打包与复现

- outputs/armbian/f8-sensors-f2/f8-sensors-f2.tar.gz：10个文件、服务启用软链接、manifest、驱动源码；是增量根文件包，不能当 BOOT 刷写。
- manifest.json：目标路径、来源、哈希、明确Linux文件模式；acceptance.json：最终用户反馈和验收界限。
- tools/package-f8-sensors-f2.py：生成包并核对归档内哈希/权限。
- tools/install-f8-sensors-f2-root.py --root <Linux根目录>：root执行，复制程序和模块、建立目标链接并运行depmod；tools/configure-f8-release-root.py 已调用该脚本。
- 个人磁场及光学校准保留在本机账户，不复制进新账户或发布包。新用户需自行校准。

归档SHA256：44f245f9ddb3977ca696d7a4365bcd209606d891681c8945104ba1b527188262。

## 证据与验证界限

local/hardware/：optical-dark01.json、optical-indoor01.json、sensors-f2-live-verify01.json、fusion-timestamp-verify01.json；最终视觉布局 sensors-f2-final.png。更早 sensors-f2-final01.json 的失败仅为重启已关闭的临时GUI单元，后续已重新打开验证；初次安装Node超时来自输出管道未排空，并非设备安装失败。

tools/test-f8-sensor-fusion.py、tools/test-f8-sensor-example-math.py 通过；数学覆盖姿态/重力/航向/倾斜、时序偏差和失效路径；修改Python语法检查、离屏渲染和现场数据检查通过。归档10文件与源码/overlay逐项哈希、权限和服务链接验证通过，发布钩子仅一处。

尚未验证冷启动、系统挂起恢复、新账户及新刷完整镜像。模块含挂起/恢复路径，但不能称已通过实际休眠测试。不得据此宣称标准lux/cm、自动亮度、系统级融合接口或指南针精确真北已完成。

## 回退与接续注意

原程序与原校准备份在平板 /var/lib/f8-pro/backups/sensors-f2/；后续保存校准有时间戳备份。回退先停用f8-optical.service，确认3-0024确由f8-em30918驱动后删除该I2C客户端，再卸载模块；驱动卸载恢复初始配置。按备份恢复原程序/个人校准，勿盲目覆盖后续用户校准。未修改BOOT，无需为了本轮回退重刷BOOT。

后续优先在下次正常重启时顺带核对服务和新校准加载，不要求用户现在重复测试。电池继续暂缓；扬声器音量曲线实验已撤回，不得自动重启；相机禁止热重绑CIF/DPHY/ISP；保留现有触摸/旋转矩阵和充电策略。
