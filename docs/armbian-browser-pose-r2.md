# F8 浏览器姿态兼容 R2（2026-11-03）

## 已完成与用户确认

用户报告 CoderTools 页在绕同一条边旋转时混入别的轴，停住后慢慢恢复；F8 系统观察工具转动正常。R1之前验证的是浏览器能读到数据，未覆盖这种动态正确性。现已分别处理浏览器融合算法和该站绘制问题，用户最终确认：

- 姿态直通后：“转轴和停住后的姿态都正常”。
- 页面绘制修正后：“明显跳动已消失，转动正常”。

已固化到现有“Chromium（相机兼容）”入口/usr/local/bin/f8-chromium-camera，并纳入后续ROOTFS发布。原兼容浏览器需要完全退出后重开一次才会采用新启动器；未强制关闭原浏览器窗口，独立测试窗口仍可继续用。无需刷BOOT。用户设置及磁场、光学、当前boot陀螺仪校准均未改动。

## 问题一：Chromium Linux的姿态融合

已下载核对实际156.0.8078.73版本 relative_orientation_euler_angles_fusion_algorithm_using_accelerometer_and_gyroscope.cc。其相对欧拉角滤波把gyro_x对应的角与accel_x分量混合，另一轴用accel_y；与正确重力投影不对应。单轴+X倾斜并保持时，会逐渐衰减X角，同时在另一轴出现角度。这与用户描述及离线回归一致，不能通过把原始IIO坐标乱换一遍来同时保证各API正确。

R2以官方[CDP传感器通道](https://chromedevtools.github.io/devtools-protocol/tot/Emulation/#method-setSensorOverrideReadings)承载实时F8融合四元数，直接提供relative-orientation/absolute-orientation，绕开浏览器有问题的再次融合。原始加速度、角速度、磁场继续走R1标准IIO通道，不改变坐标轴或比例。旧deviceorientation事件由浏览器自己的四元数转角链路得到正确角度，不另启DeviceOrientation覆盖域（该域与Emulation同一虚拟传感器会冲突，原型测试已发现并移除）。

源码依据：[Chromium156融合算法](https://github.com/chromium/chromium/blob/156.0.8078.73/services/device/generic_sensor/relative_orientation_euler_angles_fusion_algorithm_using_accelerometer_and_gyroscope.cc)。缓存位于analysis/armbian/browser-sensors/156.0.8078.73/。离线测试覆盖单轴保持、500组四元数/欧拉角回转、三个轴和90°附近/翻面的角度。

## 姿态直通实现

新增armbian/sensor-relay/browser_pose_bridge.py及browser_pose_math.py。原相机启动器保留独立profile、原相机LD_PRELOAD、Wayland、额外传感器开关，改为父进程启动Chromium子进程，通过仅父子持有的文件描述符3/4双向管道通信；不开放TCP调试端口，不向网页注入通用传感器API替身，不授予站点权限。

父进程从当前用户D-Bus net.f8.Sensors/GetSnapshot读取真实融合结果，wxyz转换为网页xyzw。只替换相对/绝对姿态两类后端；新页面/子框架自动挂接。其他浏览器或普通Chromium启动配置未改。主浏览器完全关闭后父进程退出；旧profile已有浏览器进程时，Chromium的singleton转发仍可能让新参数不生效，所以必须完全退出该兼容实例再重开。

正常源有效且测量龄期小于0.65秒时直通；短时源读数缺失可保持上次真实姿态至1.2秒并标记held_while_source_recovers，超时撤回可用性。显式关闭中继立即撤回，不能借保持机制绕过用户开关。重新开启中继后若页面Sensor对象已报错，需重新点开始或刷新页面。

读取D-Bus后再计算龄期，修正原型中“请求前时间早于最新源时间”导致短暂负龄期而被误拒绝的问题。当前运行状态写入/run/user/UID/f8-browser-pose.json（0600），含源时间、可用性、是否短时保持、协议错误和近期可用性变化，不含浏览历史或网页正文。

浏览器通道是软件中继，不是把硬件采样提高到20Hz以上；发布目标最高20Hz，实际新姿态受物理IIO轮询限制。传感器timestamp是浏览器接收/发布时刻，诊断文件另保留源单调时钟时间。绝对姿态仍要求有效三轴磁场校准和可信磁参考；磁场不可信时绝对模式可用性会撤回，不输出假磁北。

## 权限与实测

隔离测试用真实硬件、临时profile和secure loopback页面，保留默认沙箱。最终一次授权测试：相对姿态30次、绝对姿态31次，无协议或传感器错误，旧deviceorientation约[0,-3.1,1.4]°，与F8融合角一致。单独拒绝accelerometer权限后，相对/绝对均0数据，得到NotAllowedError；旧事件仅允许全null占位，没有姿态值。Permissions-Policy明确禁用传感器的子页面0姿态数据，得到SecurityError。

因此未借CDP授予网页权限或绕过子页面传感器策略。不得以后为“修复无数据”加入自动grantPermissions、关闭沙箱或root浏览器。

证据local/hardware/browser-pose-pipe04.json。早期pipe01/02原型因覆盖域冲突或龄期判断而有NotReadableError，pipe03有诊断列表切片错误；这些均非最终验收结果，应保留历史，不能拿来声称最终通道不稳定。

## 问题二：CoderTools立方体跨界跳转

用户随后报告偶尔明显跳过大角度再恢复。同步记录160帧：0无效、fusion gap_count=0，观察到的最大帧间隔约0.158秒；捕捉到航向0.023°到355.012°，实际变化仅约5°。未发现需要用强滤波遮盖的采样重置。

读取用户指定公开页面及版本JS后确认：立方体使用rotateX(-beta) rotateY(gamma) rotateZ(alpha)，并有transition: transform 0.05s ease-out。数值跨0/360会被当作长路径插值；欧拉变换顺序也与W3C Z-X-Y组合不一致。

新增codertools-motion-fix.js：仅匹配codertools.net或www.codertools.net且路径/tools/motion-sensor-test.php，读取该页#cube3d已经写入的角度字符串，按W3C Rz(alpha)*Rx(beta)*Ry(gamma)转换并作CSS轴变换S*R*S（S=diag(1,-1,1)），写为等价matrix3d，并禁用该元素过渡动画。MutationObserver在绘制前修正，已是矩阵则退出以避免循环。

不改变网页传感器数值、权限或其他站点。若将来该站更换元素ID/变换格式，局部绘制修正需复查；姿态直通本身不依赖该站。Node回归验证了各轴、0/360跨界、90°/140°、与四元数矩阵等价及无关主机不生效。用户重复绕边、转向跨起始方向后确认明显跳动消失。

公开页：https://www.codertools.net/tools/motion-sensor-test.php?lang=zh 。版本JS参数9409a637a5fc4bf4ce4d1e192f1b101a；原文缓存analysis/armbian/browser-sensors/codertools-motion/。注：该页立方体实际读取的是旧deviceorientation事件，不能仅凭页面标“Generic Sensor API”就推断立方体直接使用RelativeOrientationSensor。

## 安装、发布与回退

R2共23个受清单跟踪的根文件，相对R1只新增browser_pose_bridge.py、browser_pose_math.py、codertools-motion-fix.js并更新现有浏览器启动器。内核模块、IIO中继、自动亮度、传感器融合校准数据未改。

- outputs/armbian/f8-sensor-relay-r2/f8-sensor-relay-r2.tar.gz：增量根文件、清单及源码；需已有F2基础和匹配6.1.115内核，非BOOT或完整ROOTFS。
- SHA256：5ca2463430ec497957d8828fa0b3d7a3b70f9774c6b53eac2103af90e64f4b18。
- tools/prepare-f8-sensor-relay.py、package-f8-sensor-relay.py、install-f8-sensor-relay-root.py已指向R2。沿用R1已验证的内核模块及其module-check.json，没有重新构建/加载内核模块。root发布钩子仍调用通用安装器。
- 23文件实机及overlay哈希匹配，临时根重复安装/权限/链接验证通过；数学、页面矩阵、真实浏览器与用户动作测试通过。个人校准不打包。
- 原R1归档和验收保留不改写。平板/var/lib/f8-pro/backups/sensor-relay-r2/保留被覆盖文件；回退先退出修复后的兼容浏览器，恢复R1启动器即可回到旧浏览器后端。三个新增文件可随回退移除，保留现有传感器服务、用户设置和校准。

当前独立测试进程f8-browser-pose-r2-live.service，profile在用户.cache/f8-browser-pose-test/profile。它已获物理动作验收，非日常兼容profile；不清理或关闭用户原有窗口。正常入口更新已安装，下一次完全重开即采用R2。

未重打完整ROOTFS，未验证冷启动、新账户/全新刷机、全部第三方站点或本轮相机物理回归。自动亮度保持R1已验收状态；电池、触摸、系统旋转矩阵、摄像头CIF/DPHY/ISP均未改动。
