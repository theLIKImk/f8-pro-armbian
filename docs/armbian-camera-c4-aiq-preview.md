# C4后摄3A／预览最新接续（2026-11-01）

> 2026-11-02更新：拍照与无声录像现已实测通过，且前摄已接入镜头选择器。当前状态请以[前摄C4记录](armbian-camera-front-c4.md)和[相机软件记录](armbian-camera-kamoso.md)为准；下方“前摄未接入”“只保存画面”等为该日期历史状态，不覆盖新记录。

本文覆盖旧`armbian-camera-c4-result.md`中“后摄3A只2帧、尚未修复”的状态。BOOT方法单独见`BOOT-BUILD-GUIDE.md`。本阶段没有重新刷机或重启，C4 BOOT仍为SHA256 `fbbfa1ec…6c0903a`，boot ID仍`532eb6df-13ce-4e63-9645-24d4136d96b9`，最后SSH 192.0.2.227 / f8test。

## 已解决的两项后摄问题

1. **2帧后停流：**trace证实RKAIQ每帧把后摄VBLANK写回26，覆盖一次性设置64行；在线ISP要求消隐至少1000µs，默认只有700µs。原厂IQ的`ae_calib.CommCtrl.AecFrameRateMode`为`isFpsFix=0/FpsValue=0`。派生文件只把两项改为1/14，由AE自身维持14fps，连续45帧成功。仅在开机设置一次VBLANK不足以解决3A运行中覆盖问题。
2. **AWB三通道为0及LSC src0×0：**实机`RKMODULE_GET_MODULE_INFO`返回OV8858 AWB flag=1，测量r=314/b=299/gr=512/gb=512，但四个golden值全0；LSC flag=1、8×10旧网格，width/height/table_size全0。程序实际提交的ISP参数也证实R/Gr/B增益为0。运行库API虽可读回手动增益，仍会被不完整OTP处理污染。

已用仅相机进程加载的`armbian/camera/aiq-otp-validate.c`验证：成功读取目标模组信息后，只把不完整AWB/LSC块的有效flag清零，让RKAIQ使用IQ文件中的校准；不改传感器OTP、原始数值、驱动或内核。严格匹配OV8858及HS5885-BNSM1018-V01，ABI大小静态断言5207。这是应用内兼容处理，其他程序直接读取内核仍会看到原始OTP描述；后续可评估正式驱动／上游用户态修复。

组合“14fps派生IQ＋拒用不完整OTP”后，后摄45帧正常，零AWB增益／LSC尺寸错误消失。普通用户f8test连续140帧保持14fps，平均Y采样从16.15收敛到约98；用户实际反馈**颜色正常**。未做色卡、精确色温或长期稳定性量化验收。

## 正在使用的隔离运行时

- RKAIQ：Seeed v1.0发布包中的AIQ v6.0x8.0 / 2024-09-13。
- `/opt/f8-pro-camera/aiq-v6-c4/lib/librkaiq.so`，SHA `a5e75defe32219c397aae1f7b6b6935924d7ed7a594936ff22dac377b9096816`。
- 同目录`libf8-aiq-otp.so`，SHA `8993fc7ed9759ca49aa7a6c38050700b125b18c55d6079bce28f6de910915f2b`。
- 派生IQ：`/opt/f8-pro-camera/aiq-v6-c4/iqfiles-fps14/ov8858_HS5885-BNSM1018-V01_default.json`，SHA `7ee470f24625f01eb6eddac2e5854f7c148107c1146ff3c8dc260c3ba50cbe9f`；除两项AE帧率策略外保持原厂内容，AWB仍AUTO。
- 原始IQ保留在`…/iqfiles/`。不向`/etc/iqfiles`安装这轮试验软链接，不替换全局库，不设3A开机自启动。
- 模块启动服务仍为C4上一阶段的camera-start SHA `791d0bcf…7ff2a20`、unit SHA `c4350f04…d1f83ccc`。

## 用户预览程序

桌面及菜单新增“F8 相机预览”，窗口标题“F8 后置相机测试”。当前只开放后摄；前摄画质适配中。

- 启动入口：`/usr/local/bin/f8-camera-preview`。
- 前端源码：`armbian/camera/camera-preview.py`，安装`/usr/local/lib/f8-pro/camera-preview.py`。
- worker源码：`armbian/camera/aiq-backend.py`，安装同一目录；SHA `84e9068d0cd01463126b7067dc3f84f3893b5e1a455c703a73a007655966286b`。
- worker用私有RKAIQ与OTP验证库；通过sysfs实体路径识别后摄ISP mainpath，C4守卫，不硬编码新boot ID。
- 前端使用标准v4l2-ctl输出NV12到管道，再用`camera-pixels.c`转RGB并交给PyQt6；没有使用GStreamer摄像头源。后者在本机测试时启动流但不交付帧，暂不采用。
- `/usr/local/lib/f8-pro/libf8-camera-pixels.so` SHA `ef077246c1088cff2d3de8e69730430818fe2ad8c62215408e0380ba5ee7afaf`。真实帧与FFmpeg full-range BT.601、相同最近邻色度上采样比较，平均差0.221／255、最大2／255。与默认双线性上采样的边缘差异不能误判为矩阵错误。
- 普通用户Wayland窗口smoke05接收176帧，截图实看通过；关闭后worker exit0、正常deinit，engine/capture pid均0。V4L2采集进程收到主动SIGINT时Qt显示CrashExit属于预期停止，不是崩溃；已避免把它误报为错误。
- 手动“保存画面”保存640×480预览PNG到`~/Pictures/F8Camera/`；源代码路径已实现，用户尚未明确确认保存成功。不是全分辨率拍照。
- 状态：`/run/user/1601/f8-camera-preview-status.json`。不开机自弹、不自动录像；用户打开APP并点击预览才启动采集，关闭停止worker。

## 用户刚给出的方向反馈

用户反馈“颜色正常，画面倒置”。已把后摄前端默认“旋转180°”设为勾选，保存画面使用同一旋转。当前安装前端SHA为`6d31a7742205c96ca112a58b6ee604b2ed44b02d1d98602c9283b284b097a471`。

方向改动只在root前端程序，不改BOOT、自动旋转矩阵或传感器Bayer格式。已经运行的旧窗口还需手动勾选或关闭重开才能用新默认值；本轮没有为此强行关闭用户窗口。**新默认方向的用户二次验收仍待。**

通过用户systemd transient unit `f8-camera-preview-review01`打开的窗口仍按用户操作运行。本轮随后转去整理BOOT构建说明，没有继续操作相机或安排重启。

## 排除／失败的试验，避免重复

- RKAIQ6.0x32.0普通测试同样2帧；其RT统计线程因当前会话RT调度EPERM不能创建。单进程SCHED_OTHER回退能创建线程，但仍不解决停流。正常工作路径不使用这个调度回退库，也不使用v32库；系统CPU与调度策略未改。
- 旧包UAPI2.5与kernel2.9有差异，但AArch64实际布局：params10825/10921，统计16172相同，AWB等关键偏移一致。96字节主要在参数尾部新增exposure，不能据此宣称已证明接口不兼容是根因。
- 对照原厂Ubuntu镜像提取的AIQ5.0x1.3已审计依赖和API，隔离调用init失败；没有全局安装或推广为修复。
- 普通用户早先init SIGSEGV，trace定位`/tmp/aiq0.lock`是root试验遗留，O_CREAT|O_TRUNC被EACCES拒绝，库未处理错误。只在fuser确认无人使用、文件为root普通文件且非链接后删除了该临时旧锁，普通用户自行重建。没有放宽全局权限／关闭protected_regular。以后不要再混用root试验与普通用户3A制造锁冲突。
- `aiq-param-tap.c`只是进程内部参数只读调试，正常worker不加载它；中途关流后mmap已释放，所以需流中采样。
- 源码／测试工具多有固定boot ID、一次性输出和安装守卫；不要直接把历史test脚本当通用安装器重复执行。

## 核心证据

`local/hardware/`中的：

- `camera-c4-otp01.json`、`back-aiq-trace01.txt`、`camera-c4-params/params-tap-*.bin`。
- `camera-c4-aiq-fps14-test01.json`、`camera-c4-aiq-otp-test01.json`。
- `camera-c4-aiq-otp-user-long-02-test01.json`（140帧）。
- `camera-c4-preview-smoke05.json`（176帧、关闭清理通过）。
- `camera-c4-preview-update06.json`（默认方向改动）。
- `camera-c4-runtime01.json`（系统0failed、无内核Oops，方向改动前的root清单）。

`local/hardware/camera-c4-frames/`保存用户现场帧及窗口截图，仅用于本机验收；不放进通用发布包。初次smoke01因漏import sys失败，02/03因GStreamer源不交付帧失败；不要把空文件或旧失败日志覆盖最新通过结果。

## 接下来

先确认用户重开后方向／保存画面；前摄仍只有原始／ISP取帧通过，其原厂IQ是scene_isp21，尚未适配ISP30。后摄调焦仍disabled，全分辨率拍照、重复开关、重启后的首次直接ISP出流及runtime完整打包验收待处理。不要复制其它模组IQ当成GC5035最终校准。

本轮额外安装strace一个包、无升级移除；没有更换BOOT／kernel，没有热重绑CIF/DPHY，没有改充电/BQ/PD、CPU频率、GPU、音频或个人指南针校准。
