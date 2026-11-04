# C1实测、相机软件与C2冷启动修正（2026-11-01）

## 当前必须保留的状态

用户已刷C1并启动，boot `d7fc7e8b-9936-4190-9b5b-3ec1a33b0576`，SSH `192.0.2.227`。用户报告没有相机软件；已安装qv4l2和GStreamer工具、创建桌面“相机测试”。**摄像头预览和拍照仍未通过。**

本轮运行中重新绑定CIF触发内核Oops。系统随后仍running/失败单元0，但这不代表内核未受影响。已停止摄像头操作并保存完整dmesg，不在本次启动继续取帧。需要用户刷C2后从新内核状态测试。未重启或代用户刷分区。

## C1实机证据

- GC5035 `5-0037`真实芯片识别成功，绑定gc5035。
- OV8858 `5-0036`在probe前因GPIO3_A6/pin102共享MCLK的pinctrl竞争失败：GC已占用该pin，OV无法再次独占申请。
- DW9714有多个新字段缺省、I2C无响应；本轮不猜新VCM电流和供电参数。
- 两条CIF路径及DPHY/CSI子设备出现，最初22个video节点、media0/1，但没有完整sensor链接。不能把这些节点当作可预览相机。
- ISP虚拟节点先probe、物理rkisp_hw稍后probe；虚拟节点返回EINVAL而非延迟probe。待物理设备绑定后，对原本**未绑定**的两个ISP虚拟节点执行initial `drivers_probe`成功，出现media2/3和ISP节点。
- 随后重绑DPHY1未恢复完整GC链接。对rkcif-mipi-lvds2执行unbind/bind时，**重新bind过程中**runtime_resume触发`rkcif_do_soft_reset+0x2c`空指针，写sysfs的python进程被杀。已禁止继续热重建媒体链路。
- 实际配置`CONFIG_NO_GKI=y`，不能把参考源中`!CONFIG_NO_GKI`的早期sensor跳过分支当本机原因。图像链路未完整的原因仍需新启动后观察，未宣称已定位全部问题。

证据：camera-c1-boot01.json、camera-probes01.json、camera-isp-reprobe01.json、camera-front-reprobe01.json、camera-cif-oops-full01.json，均在local/hardware。错误的CIF热重绑脚本及DPHY热重绑脚本已在开头加无条件拒绝，勿绕过；尤其不要再次执行CIF unbind。

## 软件已安装

- qv4l2 `1.32.0-2ubuntu1`、gstreamer1.0-tools `1.28.2-1`，APT安装2个新包、0升级、0移除。
- 桌面 `/home/f8test/Desktop/f8-camera-test.desktop`，中文“相机测试”。
- 启动器 `/usr/local/bin/f8-camera-test`：正常新启动执行qv4l2；对本次已经Oops的boot ID提示先新启动，不打开媒体设备。
- 证据camera-app-install01.json、camera-c2/launcher01.json。初次GUI启动请求后为诊断关闭；不声称预览窗口出图，未保存相机画面。

## C2改动

1. 两个sensor保留原来的共享24MHz时钟consumer；将MCLK pinctrl与原电源pin的所有权统一交给共同camera电源regulator，删除sensor上的重复pinctrl声明，解决pin102独占冲突。核对两个驱动中pinctrl均为可选，未改变reset/pwdn/电压/CSI链路。
2. 暂停DW9714节点并删除后摄lens-focus引用，先验证摄像头取帧。调焦单独后续适配，不把VCM初始化错误带入本次识别测试。
3. 已在原生root安装并enable `f8-camera-start.service`。在udev settle后、SDDM前加载/等待两个sensor，核对物理ISP已绑定，然后只对**未绑定**的ISP虚拟/sditf设备做initial probe。**不包含任何unbind、reset或自动取帧。** 这项冷启动流程尚未实机验收，不能称完整链路已修好。
4. 启动服务由C2标记守卫，当前C1条件测试退出1，未启动服务；S1回退无camera标记时跳过。unit语法最终检查无输出/无告警。初版ExecCondition转义警告已通过grep条件修正并另存证据，不使用旧hash。

kernel、ramdisk、CPU cmdline、所有原CSI graph、USB/蓝牙/S1标记及原生root中指南针个人校准均保持。FIT/resource DT同步、限定差异、哈希、内存和BOOT容量通过；未做C2冷启动/芯片ID/画面验收。

## 文件与下一步

`outputs/armbian/official-f8-camera-c2/BOOT_ONLY_ARMBIAN_CAMERA_C2.img`

- 49453272字节。
- SHA256 `41b1f3f84f23107ee0de68a567406fa797de5436b65de6ab554acc538bb7247f`。
- 用户进入Loader，仅勾boot、LBA `0x00008000`；不刷rootfs/Loader，不擦除。
- C1不作为回退基线。稳定回退为S1 `outputs/armbian/official-f8-motion-s1/BOOT_ONLY_ARMBIAN_MOTION_S1.img`，仍只刷boot。

启动后先保存新boot的read-f8-camera.sh及f8-camera-start服务日志，确认前后sensor、ISP/sditf绑定和完整media链；不要在未确认链路前重复点击取帧。若仍缺链路，先读pending_async_subdevices和驱动日志；不能为恢复节点而热unbind CIF/DPHY。再选择正确的capture节点，做有界短时取帧、预览和用户验收。

RKAIQ/3A尚未安装，IQ与旧库ABI仍待核；即使有画面，曝光/白平衡、画质、调焦和拍照保存仍需要独立验收。此次新启动也将清除已触发Oops的内核状态；不是通过“失败单元0”判断摄像头安全可用。
