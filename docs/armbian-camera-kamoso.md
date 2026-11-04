# Kamoso 安装与兼容性检查（2026-11-02）

> **最新：Kamoso中继兼容已通过用户验收。** 见[兼容中继](armbian-camera-relay.md)，实时画面、拍照和录像均正常。下文“Kamoso未通过”指旧的物理ISP直连尝试，已由新的中继启动器替代，不能覆盖本条验收。

> 后续同日前摄进展见[前摄C4记录](armbian-camera-front-c4.md)：F8相机已支持前后摄选择，前摄拍照/录像实测通过，等待用户颜色与方向验收。本页保留Kamoso及最初后摄软件阶段的记录。

**最新可用入口：桌面“F8 相机（拍照录像）”。** Kamoso仍未通过；已在原专用预览中增加真正可保存、可解码的录像，使用v4l2-ctl采集，GStreamer仅负责管道编码。不能把替代入口的成功写成Kamoso通过。

## F8 相机拍照与录像已实测

- 源码`armbian/camera/camera-preview.py`；最新安装SHA256 `62e6d077a0fed0c4d5894a843c02765620a368ebf2c5d60a5c070de41377308f`，命令仍`f8-camera-preview`，桌面改名但文件名未变。
- 后摄640×480、14fps；拍照PNG到`~/Pictures/F8Camera/`，MJPEG/AVI录像到`~/Videos/F8Camera/`；当前**无音轨**，不宣称全分辨率或硬件编码。前摄／对焦仍未开放。
- NV12原始帧送入fdsrc/rawvideoparse，标记full-range色彩，旋转180°与预览一致，再videoconvert/jpegenc/avimux。不会调用卡住的GStreamer相机源，也不创建虚拟摄像头。
- 停止录像关闭编码输入，等待EOS正常写完AVI索引；关窗同样收尾并正常停采集与AIQ。编码待写队列超约1秒时停止并提示错误，防止无限堆积；异常退出／无有效帧显示失败。
- `local/hardware/camera-media-smoke01.json`：普通用户Wayland，202预览帧，PNG325167字节；5秒70帧AVI1952640字节，独立avidemux/jpegdec解码70帧并EOS，错误为空，无残留进程。
- 最终版本`camera-media-smoke02.json`：录像未满5秒时关窗，43帧AVI1134000字节，独立解码43帧并EOS；另保存PNG，app exit0、AIQ exit0、engine/capture PID0，无残留。主动SIGINT结束v4l2-ctl的Qt CrashExit2为既有预期停止行为。
- 测试图像只留在平板`~/.cache/f8-camera-media-test01/`与`test02/`，没有上传或打包发布。用户方向／手动保存／长录像仍待反馈。
- 收尾`camera-media-runtime01.json`：0 failed、当前dmesg未见Oops，专用APP已重新打开供用户试用，未自动采集。tainted=4608（旧boot曾4096）；`camera-media-kernel-warnings01.json`当前日志没有WARNING块，原因不能据此确定，不能宣称整次boot无警告。未为此额外重启。

## Kamoso 诊断记录

已安装发行版 Kamoso 25.12.3-0ubuntu1 与 gstreamer1.0-qt6；仅新增这两个包，无升级或删除。桌面与菜单入口“照相与录像（Kamoso）”，执行 `/usr/local/bin/f8-kamoso`；原版程序未修改。用户最新反馈：**没有画面或画面卡住，拍照／录像未通过。** 不得将“安装成功／设备打开”记为相机应用可用。

本轮 SSH 仍为 f8test@192.0.2.227；新发现 boot ID `bbeda716-dd1f-4905-a389-62dc09d04c8d`，已不同于上一轮。cmdline 仍有相机清理及 cpufreq 黑名单；AIQ 的 C4 chosen 守卫通过。本轮没有刷写 BOOT、重启、热重绑、改充电策略。

## 已查明并处理的枚举问题

- `/dev/video22` 的 udev `ID_V4L_CAPABILITIES=:capture:` 正常，普通用户有读写权限；不需伪造属性或放宽全局权限。
- Kamoso 用 GstDeviceMonitor 的 Video/Source、video/x-raw 过滤器。
- libcamera 0.7.0 的 provider 无条件隐藏 v4l2deviceprovider，而本机 libcamera 自身没有找到可用相机，并报告无法打开 dma-buf provider。此处不以 chmod dma_heap 作为修复。
- ctypes 独立测试显式降低 libcamera provider rank、显示全部设备后，设备列表由空变非空。只设置 GST_PLUGIN_FEATURE_RANK 在这轮 provider 测试中无效，不能声称环境变量已解决。
- 启动器为 Kamoso 创建私有 GStreamer 插件视图：`~/.cache/f8-kamoso/gst-plugins`，指向发行版全部插件但排除 `libgstlibcamera.so`，独立 registry `gst-registry.bin`。不删除发行版插件、不影响其他软件。仅作用于本应用的 `GST_PLUGIN_SYSTEM_PATH_1_0` 等变量。
- 更新后不再报告 No device found，Kamoso 确实持有 video22，并开始 ISP 流；自动协商到3264×2160、NM12双平面。但用户确认仍无实时画面。

启动器源码 `armbian/camera/kamoso-launch.py`，当前安装 SHA256 `0c2e2f1293c1dae33147231b9604fb5b65656cda81d11a683eb2d5fff26a960e`。沿用私有14fps IQ与不完整OTP验证库，AIQ与窗口同生命周期，没有开机自启动。不要同时开专用预览和Kamoso。

## 流检查

`camera-kamoso-stream01.json`：固定640×480 NV12/14fps、MMAP的 gst-launch 能协商并 STREAMON，但28帧未完成，超时退出137；日志显示请求2个缓冲。紧随其后的同一AIQ进程 v4l2-ctl 虽返回0却报告 select timeout，**不能当取帧成功**。AIQ重新开始帧号时有sof disorder；结束正常deinit。下一步先用独立新AIQ测试专用v4l2路径和2/4缓冲，排除旧流状态污染，再处理GStreamer捕获。

证据在 `local/hardware/camera-kamoso-*`，包括 install01、launcher-install01、update02、provider01、libraries01、monitor02/03/04、launch02、state02、stream01。`tools/probe-f8-kamoso-stream.sh` 为有界普通用户测试，会关闭本轮Kamoso测试窗口并结束自己启动的AIQ；不是内核热重绑。该脚本会随下一轮诊断调整，以对应输出文件为准。

后续尚待：真正连续取景、照片保存、录像编码/停止/可播放、画面180°方向（专用预览已默认修正，Kamoso不继承）、前摄画质、对焦。不以枚举成功覆盖此前待办。

追加流测试：`stream02.json`新AIQ下V4L2单平面4/2缓冲及恢复4缓冲均28帧成功，2缓冲有丢帧。`stream04.json`双平面NM12及单平面NV12各28帧通过，故没有根据拒用这些格式。`stream03.json`strace确认GStreamer实际选择NM12、2缓冲并在STREAMON后poll阻塞；预热未解决。`stream05.json`仅测试进程加载`armbian/camera/gst-buffer-trial.c`，把严格匹配rkisp_v6后摄mainpath的MMAP请求从2增加到4，仍未解决。诊断库只在用户cache中，**未装入Kamoso启动器、AIQ或全局LD_PRELOAD**。后续从真实调用差异调查，不盲刷BOOT。
