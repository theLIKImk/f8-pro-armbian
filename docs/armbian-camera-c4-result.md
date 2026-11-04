# 摄像头C4真机结果：双摄取帧通过，3A未通过（2026-11-01）

## 当前设备与结论

用户确认C4启动成功，SSH只读确认boot `532eb6df-13ce-4e63-9645-24d4136d96b9`、192.0.2.227 / f8test。chosen async=c4、camera=c2（供既有服务守卫使用），U5/BT1/S1标记保持。

**C4的等待链修复已真机生效，前后摄像头均取得真实图像。尚未完成正常画质、首次启动即预览、方向、自动曝光/白平衡、调焦和拍照软件验收。**

- 约2.99秒CIF/ISP清理initcall被跳过，没有再清除未就绪项。
- 3.126秒提前加载开始；GC5035在3.229秒识别、3.234秒CIF notifier完成；OV8858在3.261秒识别、3.733秒CIF notifier完成。
- 9.65秒root服务补原来未绑定的ISP initial probe，两ISP notifier完成。
- media图出现sensor→DPHY→CSI→CIF及sditf→ISP链路。pending仅有notifier标题、无未满足的fwnode等待项，不能把标题列表误报为全链仍互等。
- 最终系统0failed、tainted=4096，没有本轮内核Oops/panic。4096不是相机完全正常证明。

## 分阶段取帧结果

1. 首次ISP 640×480 NV12：前摄超时、文件0字节；后摄8帧、3686400字节成功。注意v4l2-ctl输出`select timeout`时也可能exit0，验收必须看帧数/文件长度，不能只看退出码。
2. 前摄CIF直出：2592×1944 RG10，2帧共12939264字节成功。这证明前摄sensor/CSI/CIF可出流，不是仅芯片ID识别。
3. 默认消隐时间触发ISP-online >=1000µs警告，前933µs、后700µs。通过标准V4L2控制将前vertical_blanking设80、后64，不改供电、寄存器表、曝光或增益。
4. 此后前摄ISP再测：640×480 NV12，12帧、5529600字节成功。此前做过RAW采集且改变了blanking，**不能仅凭这次成功断言初次超时完全由blanking引起**；下一次冷启动仍需验证无需RAW预热即可直接ISP预览。
5. 最后帧由NV12正常转换PNG并实际查看，确有场景，不是假测试图。原始亮度偏暗；前摄图像观察到倒置，尚未按平板实际朝向做用户确认。没有对PNG做提亮后冒充原始画质。

本地帧与预览在`local/hardware/camera-c4-frames/`；这些是用户现场图像，不应放进通用发布包。平板临时帧在`/run/f8-camera-c4/`，重启会清空。未设置自动拍摄或持续录像。

## 消隐时序持久化

`armbian/camera/camera-start.py`已增加**仅C4**执行的标准V4L2 S/G_CTRL步骤，按实体名寻找sensor subdev，前最少80行、后最少64行；已有更大值保持。使用Python fcntl避免新版v4l-utils向6.1内核发送可选SUBDEV_S_CLIENT_CAP时的ENOTTY/exit255干扰判断。

- 已安装`/usr/libexec/f8-pro/camera-start.py`：SHA256 `791d0bcf4bbf7d7f16b25691bdc0c5f33aa89a9b44ee4bc3b9b495f147ff2a20`。
- 旧版保存在`/var/lib/f8-pro/backups/camera-start-before-c4.py`。
- service unit保持SHA `c4350f0435fe3f4b1c3c1dacc1e9ec59849a7ec7b1470dc1b34b9f14d1f83ccc`，原有enable状态保持。
- 已在所有media设备均bound的前提下手动运行一次新版脚本，确认不发生initial probe/unbind，控制读回成功；没有重启unit或系统。
- **下一次开机自动应用仍待冷启动验收**，不能把本次手动验证当成重启测试通过。

## RKAIQ试验与限制

从[Seeed官方RK3588软件包发布页](https://github.com/Seeed-Studio/seeed_armbian_extension/releases/tag/v1.0)取得ISP30专用包，审计其ELF依赖、版本和维护脚本后，只将3A程序、librkaiq.so及两份准确原厂IQ放在`/opt/f8-pro-camera/aiq-v6-c4/`。没有执行deb维护脚本，没有替换全局库、GPU或服务，没有设置自启动。板端ldd依赖解析通过，版本AIQ v6.0x8.0 / 2024-09-13；包和文件哈希见`outputs/armbian/camera-aiq-c4-trial/manifest.json`。

发现重要区别：

- 原厂GC5035 IQ的sub_scene是 **scene_isp21**。
- 原厂OV8858 IQ的sub_scene是 **scene_isp30**。
- 顶层JSON键相同不代表ISP算法schema兼容。前摄旧IQ不能直接作为ISP30调参文件使用，不能改个键名或换其它sensor的校准伪装成功。

通用双摄`rkaiq_3A_server`试运行出现`lost smartRun para in json`后以SIGSEGV退出，属于**用户态程序崩溃**，没有内核Oops。schema不匹配是重要发现，但未取得崩溃回溯，不能认定已经证明唯一原因。该通用试验脚本已无条件禁用，防止重复运行。

后摄专用ctypes harness依据随包公开API头逐项声明签名，正确识别OV实体，preInit_scene/init/prepare/start返回成功，并正常stop/deinit。但计划45帧的测试只得到2帧后select timeout，伴有LSC尺寸`src 0x0/dst 3264x990`及AWB gain错误：**后摄3A也未通过**，不能开启自启动。下一步需核对库与实际6.1 ISP UAPI/模式、统计和参数队列，以及IQ在ISP30上的有效字段，而非继续盲调亮度。

曾为通用server创建的两条`/etc/iqfiles`试验软链接已按精确目标核验后移除；原始IQ在隔离目录完整保留。两次试验进程均已退出，没有3A常驻，没有安装服务。后摄试验可能改变本boot中的ISP状态，不能把当前状态当作干净冷启动基线。

## 下一步顺序

1. 保留C4，不再刷失败C3，不重编/替换已验证官方Image，不重刷root。
2. 后续先解决后摄ISP30算法库与内核UAPI/统计/参数流兼容，再验证连续帧和亮度/白平衡收敛。
3. 为前摄找到/构建真正的ISP30适配IQ或可靠转换流程，保留原厂文件；不直接拿其它模组IQ当最终校准。
4. 后续安排一次冷启动，验证持久化blanking和首次ISP直接出流；不需用户先跑RAW预热。
5. 再做前后预览切换、屏幕方向、实际拍照保存；后摄调焦仍禁用，单独后续处理。

继续禁止CIF/DPHY热重绑。其他硬件配置、个人指南针校准、CPU保守参数保持；充电/BQ/PD继续暂缓。

## 本轮证据

- `camera-c4-boot01.json`、`camera-c4-formats01.json`。
- `camera-c4-isp-capture01.json`、`camera-c4-front-raw01.json`、`camera-c4-front-isp03.json`。
- `camera-c4-front-isp02.json`是runner断言时留下的空文件，**不是有效测试证据**。当时v4l2控制已经设置并读回，但新可选ioctl的exit255被脚本误当失败；随后按明确读回值校验后继续。
- `camera-c4-aiq-stage01.json`、`camera-c4-aiq-install01.json`、`camera-c4-aiq-test01.json`、`camera-c4-back-aiq-test02.json`。
- `camera-c4-root-update01.json`、`camera-c4-root-verify01.json`。

以上均位于`local/hardware/`。当前没有构建、自动重启或采集后台任务。
