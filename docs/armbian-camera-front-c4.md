# C4 前置 GC5035 接续（2026-11-02）

> 后续[兼容中继](armbian-camera-relay.md)也已完成：F8前后摄可转发到标准虚拟摄像头，Kamoso取景／拍照／录像用户验收通过。当前前端哈希与启动入口以中继文档为准，下方保留前摄接入阶段资产记录。

**用户已验收：**反馈“颜色和方向正常，除了有点偏淡”，并在问答中确认“颜色和方向都正常”。前摄实时画面与上下方向基础验收通过。偏淡同时存在于前后摄，保留为共同画质优化项，不等同于精确色彩校准已完成。

已核对共享转换：前摄原厂CSM为full_range=1、BT.601系数；后摄CSM为AUTO/full_range=1；两者CGC不启用YUV限幅，CPROC的contrast/saturation均为128默认值。当前`camera-pixels.c`按全范围BT.601转换。因此现有证据不支持直接改成limited-range来“增艳”；实际ISP参数是否完全遵循AUTO配置、色卡对照、对比度/饱和度优化仍待专门验证，未改驱动或公共颜色矩阵。下方待办中的实时画面/方向等待项由此验收记录覆盖。

本轮没有改BOOT、内核、DT、供电策略或CPU频率，也没有热重绑CIF/DPHY。SSH仍`f8test@192.0.2.227`，boot ID `bbeda716-dd1f-4905-a389-62dc09d04c8d`。

## 已通过

- 前置GC5035 I2C5 5-0037，通过CIF2/DPHY1接ISP1，当前mainpath `/dev/video31`，传感器`/dev/v4l-subdev2`，完整输入2592×1944。普通用户有访问权限。
- 私有AIQ v6.0x8.0加载转换后的开发配置，连续两轮各112帧，640×480 NV12、约14fps，正常stop/deinit。AE更新曝光／增益及blanking，消隐保持在安全范围内；不是一次性设置后被算法覆盖。
- 第一轮图像分块与条纹，日志明确`src.lsc_sect_size_x[8]=0`。原ISP21的LSC扇区是8项半幅，ISP30需要16项全幅；按`half + reversed(half)`展开。对每种分辨率验证16项均正且总和等于完整宽高，原GC5035的17×17四通道增益表未修改。第二轮日志该错误消失，实看图像分块消失。
- 已接入桌面“F8 相机（拍照录像）”上方前后摄选择器。停止预览后可切换，预览／录像期间禁用选择器，沿用同一互斥锁避免两个AIQ同时占用。切换清除旧镜头画面，防止保存错相机的旧帧。前后摄默认旋转180°，前摄实际方向待用户验收。
- `camera-front-media-smoke03.json`：前摄Wayland预览110帧，PNG保存成功，5秒70帧AVI独立解码70帧并EOS；同一最终版本随后后摄42帧、录制中关窗27帧AVI独立解码27帧并EOS。均app exit0、AIQ正常deinit、record_error/last_error为空，无残留采集进程。当前仍无音轨、640×480/14fps。

## 配置如何生成

原厂前摄文件`gc5035_XHG-RKX11F-V5_HR232H65.json`只有scene_isp21，SHA256 `a74f673e0a347f3438e14fef19806041a492139b1251f90f3289975fe35c28e1`。不能简单改scene名称或将其它传感器完整IQ重命名。

`tools/build-f8-front-iq-trial.py`保留前摄sensor_calib/module_calib，以及共享版本的AE、WB、CCM、黑电平、LSC表等18个模块。差异处理为：

- AE固定14fps，匹配现有录像时基并留足消隐。
- LSC仅转换8→16扇区几何，不替换模组校准表。
- gamma生成通用2.2曲线／ISP30 log49节点，属于初期显示策略，不宣称原厂最终调色。
- ISP30新增版本的降噪、锐化、DRC、AF、CAC等模块仅借同版本后摄文件作结构占位，全部禁用；HDR也未开启。未使用后摄的WB、CCM或LSC校准。这些占位模块不能据此当成GC5035已完成生产调校。

第一版输出`outputs/armbian/camera-front-c4-trial/`保留，LSC几何不兼容，不再使用。当前第二版输出`outputs/armbian/camera-front-c4-trial02/`，结果SHA256 `94133d191ed54a65130082110ea6b45c887ddfcefb36583cc0b7d43cf980efb6`。生成器现在生成第二版，并拒绝覆盖既有产物；需要重现时先用独立输出目录，不要删除原证据。

## 当前安装

- `/opt/f8-pro-camera/aiq-v6-c4/iqfiles-front-c4/gc5035_XHG-RKX11F-V5_HR232H65.json`：第二版SHA94133d19…980efb6，旁有development-profile-manifest.json。原厂文件与后摄私有配置未替换。
- `/usr/local/lib/f8-pro/aiq-backend.py`：SHA256 `92b9272fdb80226b654cf2c9e129191ba032b8fc19d203ad9718a34e82a4c089`，新增`--camera front/back`，默认back；动态识别对应ISP mainpath和sensor实体，分别prepare2592×1944与3264×2448。
- `/usr/local/lib/f8-pro/camera-preview.py`：SHA256 `503fd23a36a5fc09edeeeb4e4a00b94159436a4b9467f10c84bba75ceb4c5659`，新增选择器及`--camera`启动参数。菜单默认后摄，本轮试用窗口以前摄打开。
- 使用原私有librkaiq与OV OTP校验preload，后者只精确过滤不完整OV8858 OTP；没有给GC5035伪造OTP。日志前部出现OV OTP提示是库枚举相机时检查后摄，并不代表前摄加载了后摄IQ。
- 继续不开机自动启动3A，没有全局库替换，没有虚拟摄像头。Kamoso的GStreamer取流问题仍独立未解决。

## 待验收／后续

用户确认前摄实时画面、颜色与方向，手动前后切换、照片与录像保存；持续运行、重启后首次前摄、量化曝光响应／白平衡、降噪与锐化、全分辨率拍照尚待。前摄原厂Gain2Reg与当前驱动增益标度仍需专门核对，不能仅凭AE亮度收敛宣称增益标定完成。后摄对焦与充电/BQ/PD/CPU仍保留旧待办。

证据`local/hardware/camera-front-stage01.json`、profile-install01/update02、aiq-test01/02、media-smoke03、runtime03、review03；用户现场帧与窗口截图只用于本地验收，不打入发布包。
