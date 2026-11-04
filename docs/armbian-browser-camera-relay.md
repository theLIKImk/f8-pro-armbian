# Chromium相机中继兼容（2026-11-02）

## CoderTools实际网站验收

用户追加测试`https://www.codertools.net/tools/webcam-test.php?lang=zh`异常，澄清当时用的是**原来的普通Chromium**。本轮只读快照还显示F8窗口已经closed，engine/capture PID均0，video42无占用；不能将这一次报告直接认定为兼容入口的新故障，也不能仅凭它判定站点代码有错。

在确认无采集／消费者后，重新打开用户最后选择的后摄，开启中继，并通过`f8-chromium-camera`打开该网址。快照记录56帧、relay_running=true、无错误。用户随后明确回复**“有实时画面，正常”**，该实际站点取景验收通过；未据此追加声称该站点的录音／录制已测。

读取站点公开JS发现其约束为width ideal1920、height ideal1080、frameRate ideal60，可回退，不是exact强制。当前中继仍640×480／14fps。未修改站点代码、扩展或浏览器权限策略。

证据`camera-codertools-before01.json`、`camera-codertools-review01.json`、`camera-codertools-user-feedback01.json`；工具`tools/open-f8-codertools-review.sh`有关闭／无占用守卫及一次性unit，不直接当作通用启动器重复执行。常规使用仍为“F8预览并开中继 → Chromium（相机兼容）→ 网页正常授权”。

**GUI用户验收已通过：**用户明确回复“画面和带声音录像都正常”。本地测试页的正常权限流程、实时取景及带声音录像均已实际确认。下方测试阶段的“等待反馈”由本条覆盖；用户原先具体网站仍需在兼容入口中按站点权限使用，不推断所有网站都已验收。

用户先确认Kamoso实时画面／拍照／录像正常，本轮追加确认**Kamoso能够录制声音**。这是Kamoso使用系统麦克风的结果；F8专用相机的MJPEG/AVI目前仍无声，两者不要混淆。

用户反馈普通浏览器能识别相机但调用卡住。当前实际Chromium为**156.0.8078.73**（Ubuntu26.04.1构建），不是旧传感器网页排查时的151。旧传感器IIO问题仍独立待办。

## 复现与处理

- `local/hardware/camera-browser-before01.json`：video42真实虚拟设备处于capture模式，YUYV640×480／14fps。Kamoso当时已关闭，未占用设备。F8后摄持续供帧。
- `camera-browser-probe01.json`：普通用户、全新临时profile、安全本机回环页、默认沙箱。WebAPI能列出F8 Camera Relay，但第二次getUserMedia停在capture阶段，18秒内没有视频帧；F8源从1274只到1302帧，capture_pid变0。不是“枚举成功就取景成功”。
- 与精确版本Chromium源码核对，V4L2 factory枚举时会对设备节点执行open(O_RDONLY)/QUERYCAP；结合之前GStreamer探测物理节点导致供帧中断的复现，采用同一进程内设备视图做A/B测试。此处支持“物理枚举与中断有关”，没有据此宣称已定位厂商内核release路径的具体缺陷。
- 只在确认F8的capture/engine均已停止、没有avimux录像进程后，结束该已停止的F8窗口并重新打开后摄中继，恢复真实供帧；保留用户已有普通浏览器窗口和配置。
- `camera-browser-probe02.json`：为独立Chromium实例加载已有`libf8-camera-relay-view.so`，只允许其打开video42。网页收到30帧真实画面；源56→140帧，capture PID16220未变，未打断供帧。
- `camera-browser-probe03.json`：相同隔离方式，真实相机＋真实系统麦克风，52次视频帧回调；3秒MediaRecorder生成203433字节、6块、`video/webm;codecs=vp8,opus`，1条音轨；源2632→2772帧，PID不变。没有生成假的图像／音频，录像Blob只在测试页内存中，未上传或保存用户影像。

独立探针的`--use-fake-ui-for-media-stream`只自动同意该临时测试页的权限请求；没有`--use-fake-device-for-media-stream`、没有禁用沙箱。安装的用户启动器**没有自动授权参数**。探针结束关闭自己的进程组；日志中测试收尾的zygote终止信息不能误记为测试期间摄像头崩溃。

## 新入口

桌面和菜单 **Chromium（相机兼容）**，命令`/usr/local/bin/f8-chromium-camera`。

1. 先在F8相机中预览并开启兼容中继。
2. 使用这个浏览器入口访问需要相机的网站，按正常弹窗授权相机／麦克风。
3. 选择F8 Camera Relay。F8窗口需继续运行，可最小化。

启动器使用独立profile `~/.config/chromium-f8-camera`，已有浏览器profile、标签页和默认浏览器设置不变。不会读取／迁移原profile的书签、密码、Cookie。此入口的进程及子进程加载既有设备视图；GPU、网络和浏览器沙箱配置保持正常。它只看中继相机，直接USB摄像头访问没有在这个入口中开放。

普通Chromium入口仍可能重现物理设备枚举问题；本轮解决的是新增兼容入口，不能宣称所有既有Chromium进程已被修复。不要将设备视图设成全局LD_PRELOAD，也不要注入AIQ或真正捕获进程。

- 启动器源码`armbian/camera/chromium-camera-launch.py`，安装SHA256 `224975c11029a07f19499f023157f7047985f0cb924ab8089792b855e84ece82`。
- 本地测试页`/usr/local/share/f8-pro/camera-browser-test.html`，源码同名，SHA256 `d0f58012c8d2753c29ceb4bbf18354d1b731802de47e99bb8ac6c9e35e99badf`。默认打开此file页；手动启动、可选择麦克风、手动录像／下载WebM，所有预览录制在本地，不向远端提交画面。
- 浏览器启动日志`~/.cache/f8-browser-camera/browser.log`。实际浏览器日常入口不自动开相机，网页仍需正常权限。
- `camera-chromium-install01.json`与`camera-browser-review03.json`记录安装／Wayland启动。已打开本地测试页，请用户点击启动相机并允许权限，**等待GUI与实际网页反馈**；目前程序级30帧及音视频录制已通过，不能将它直接当作所有网站实测通过。

未重刷BOOT／改内核／重启／改GPU、充电、CPU策略或模组IQ。前后摄偏淡、降噪锐化、全分辨率、后摄对焦及虚拟设备冷启动持久化继续保留待办。

源码参考：[Chromium156 V4L2 factory](https://github.com/chromium/chromium/blob/156.0.8078.73/media/capture/video/linux/video_capture_device_factory_v4l2.cc)。
