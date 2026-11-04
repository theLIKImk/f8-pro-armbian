# F8 相机兼容中继（2026-11-02）

> **后续浏览器也已通过：**见[Chromium兼容入口](armbian-browser-camera-relay.md)。普通Chromium枚举会打断真实供帧，新增“Chromium（相机兼容）”独立配置入口后，网页实时画面与带声音录像用户验收正常。Kamoso用户也追加确认录音正常；F8专用AVI仍无声。下方“浏览器未验收”为该阶段历史状态。

**用户已验收：Kamoso实时画面、拍照和录像均正常。** 中继使用正在工作的真实前摄／后摄，不是测试图或虚构设备；不替换内核的ISP驱动。

## 使用

1. 打开桌面“F8 相机（拍照录像）”，选择前置或后置并开始预览。
2. 勾选“兼容中继（供其他相机软件使用）”。
3. 打开桌面“Kamoso（兼容中继）”，接收当前镜头的真实画面。

F8窗口可以最小化；需要它持续供帧。停止F8预览、关闭F8窗口或取消中继即停止转发。关闭Kamoso本身不会关闭仍在工作的F8相机。切镜头先停止预览，切换后重新开启中继；Kamoso可能需要重新打开。本轮只验收Kamoso，Chromium/网页、其他客户端和多个消费者同时读取还未验收。

## 结构与限制

真实sensor → 私有RKAIQ与已验证V4L2采集 → F8应用的NV12帧 → 旋转／转换为YUY2 → 标准v4l2loopback `/dev/video42`（F8 Camera Relay）→ Kamoso。当前640×480／14fps，前后摄择一输出，不提供虚拟麦克风。音频及更高分辨率需独立适配；先前F8专用录像是无声AVI，不能将其限制泛化成Kamoso的所有编码功能已测。

已安装的发行版DKMS模块v4l2loopback0.15.3匹配6.1.115-vendor-rk35xx，正常modprobe加载，未强制跳过版本校验、未编新内核、未刷BOOT。最终参数：

```
devices=1 video_nr=42 card_label="F8 Camera Relay" exclusive_caps=1
max_width=640 max_height=480 max_buffers=2
```

`/etc/modules-load.d/f8-camera-relay.conf`及`/etc/modprobe.d/f8-camera-relay.conf`只在启动时建立虚拟设备，**不会开机打开真实相机或转发画面**。本轮没有重启，开机加载持久化尚待实测。

## 必要的兼容处理

- GStreamer加载video4linux2插件及枚举设备时，会打开真实video/subdev节点。在这套厂商驱动上，此行为实际打断了正在采集的流（第一轮只剩3/13帧）。增加进程内设备视图后持续真实采集恢复。
- `armbian/camera/relay-device-view.c`编译为`/usr/local/lib/f8-pro/libf8-camera-relay-view.so`，SHA256 `7f0b7a33c6cc32df8117e2665218ef6c0cfa0f79b2f779f753a91d406694764e`。只给中继GStreamer进程和Kamoso加载；物理video/subdev的open返回EACCES，只允许video42。没有伪造能力或图像，也不改系统权限。这是兼容视图，不是安全沙箱。
- AIQ及真正v4l2-ctl捕获进程不加载这个视图，仍按原路径访问真实摄像头；AIQ只加载原OV OTP验证库。
- 先前libcamera provider隐藏V4L2的处理继续保持为Kamoso私有插件目录，不删除发行版插件或修改全局环境。
- 最初虚拟设备4缓冲曾首次读到1帧后分配失败；只在确认video42无使用者且虚拟节点只有它时，卸载／重载了**虚拟loopback模块**恢复默认2缓冲。没有热重绑CIF、DPHY、ISP。试用rw输出没有让虚拟设备切到capture，已弃用，最终为默认MMAP输出。

## 当前程序

- F8前端`/usr/local/lib/f8-pro/camera-preview.py` SHA256 `a37dc08ad7494c34c3330db8b2530db00617d6213dcccb57fdc59bd9601d6575`，新增复选框及`--relay`；应用关闭会正常关闭中继并清理采集／AIQ。队列超约1秒会停止并报错，不无限积压。
- Kamoso启动器改为`armbian/camera/kamoso-relay-launch.py`，安装`/usr/local/bin/f8-kamoso`，SHA256 `e980743f050a2bebcf3c6933473df7898198416952c4b109d6e8adb52db71df8`。要求用户已启用中继，不再另起AIQ或关闭供帧窗口。旧直连失败入口备份在`/usr/local/lib/f8-pro/kamoso-direct-launch.py`，不应当作当前启动方法。
- Kamoso独立配置`~/.cache/f8-kamoso/relay-config/kamosorc`选择video42、关闭额外镜像，保留原日常配置；私有registry为gst-relay-registry.bin。日志`~/.cache/f8-kamoso/relay-*.log`。
- AIQ后端及前后摄IQ与上一轮相同，未为中继改动模组校准。

## 验证与证据

- `local/hardware/camera-relay-prerequisites01.json`：原有匹配模块及可用头文件；前摄原预览已达3780帧。
- `camera-relay-smoke05.json`：最终2缓冲，前摄真实供帧144帧／后摄148帧；标准GStreamer v4l2src消费者分别读28帧、正常EOS/exit0，无中继错误，关闭后无残留。
- `camera-relay-kamoso-review01.json`：Kamoso打开后源画面仍从14帧增长到84帧，writer和Kamoso均持有video42，日志无错误。
- 用户明确选择“实时画面、拍照和录像都正常”，作为Kamoso实际功能验收。未声称所有软件已兼容或全分辨率／长时间稳定性通过。
- `camera-relay-smoke01/02/03/04`保留失败／探索记录，不能当成最终通过；最新05覆盖。前后摄偏淡、前摄降噪锐化开发配置、后摄对焦等原待办仍保留。

机制参考：[v4l2loopback官方说明](https://github.com/v4l2loopback/v4l2loopback)、[GStreamer v4l2sink](https://gstreamer.freedesktop.org/documentation/video4linux2/v4l2sink.html)。
