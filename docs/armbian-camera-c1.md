# 前后摄像头 C1：原厂接线与图像链路（2026-11-01）

**C1已实测：前GC识别、后OV共享MCLK pin102冲突、ISP初始probe顺序失败。qv4l2已安装，但尚无预览。CIF热重绑触发Oops，当前内核不再测试摄像头；已准备C2修正版及冷启动服务，待用户只刷BOOT。先读 [C2交接](armbian-camera-c2.md)，下方待刷C1为历史。**

## 当前状态

用户要求开始适配摄像头。已完成只读基线、原厂DT与6.1驱动检查、C1 BOOT构建及离线验证、真机引脚空闲和现有模块检查。**尚未刷入C1、读取芯片ID、取帧、预览或拍照；不能把构建通过当摄像头可用。**

当前仍S1 boot `62ae5abd-745b-4b3a-85f4-5910371868b0`，SSH `192.0.2.227`。前后摄、ISP图像节点均未创建；摄像头I2C5 disabled，默认引脚m0也与原厂m3不同。没有启动摄像头、写I2C摄像头寄存器或采集画面。

## 板级证据

- 前摄GC5035：I2C5 0x37，模块`XHG-RKX11F-V5`，镜头`HR232H65`；2条数据lane，24MHz时钟。
- 后摄OV8858：I2C5 0x36，模块`HS5885-BNSM1018-V01`，镜头`default`；2条数据lane，24MHz时钟。
- I2C5实际地址为 **fead0000**，原厂m3 GPIO1_B6/B7（bank1 pin14/15），与触摸I2C4 feac0000区分。初始基线采集器误选了feac节点，已修正，实际C1构建使用fead。
- MCLK原厂`CLK_MIPI_CAMARAOUT_M1`、pinctrl`mipim1-camera1-clk`，GPIO3_A6（bank3 pin6）。
- 前摄reset GPIO1_B2、pwdn GPIO1_A6；后摄reset GPIO1_B3、pwdn GPIO1_A7，沿用原厂极性。
- 共同电源门控`vcc-mipidcphy-regulator`：GPIO1_A4、active-high，vin指向本机DCDC_REG8（vcc_3v3_s3），保持原厂供电关系和约束，不猜测其他2.8/1.8V轨或修改PMIC电压。
- 后摄VCM：DW9714 I2C5 0x0c，参数沿原厂；C1接入但调焦仍未验收。闪光灯引用本次不启用。
- 当前真机8个相关引脚36/38/39/42/43/46/47/102均MUX/GPIO unclaimed。

原厂链路：

```
前GC5035 → csi2-dphy1 → mipi2-csi2 → rkcif-mipi-lvds2 → sditf → rkisp1-vir0
后OV8858 → csi2-dphy2 → mipi3-csi2 → rkcif-mipi-lvds3 → sditf → rkisp0-vir0
```

只迁移原厂板级资源与graph；6.1 SoC硬件节点的clocks/resets/power-domains/compatible保持配套内核定义，不把旧5.10硬件节点整块覆盖。摄像头使用CSI2 DPHY split线路，不启用参考板中不同摄像头的DCPHY0/4-lane方案。`reference-tablet-camera.dtsi`只是6.1框架对照，里面s5k3l6、I2C6、不同GPIO与本机不符，没有照搬。

## 构建与验证

`tools/build-f8-camera-c1.py` 基于已验证S1，启用I2C5 m3、两个摄像头/VCM、电源门控、两条CSI/CIF/ISP链及对应IOMMU。新增所有phandle按实际节点路径翻译，pin配置也翻译，不复制旧整数phandle；16个endpoint方向均验证互相引用。USB PHY物理子节点顺序保持。

kernel、ramdisk、CPU cmdline黑名单、USB U5/蓝牙BT1/传感器S1标记不变。原生root中的音频、指南针APP v4及个人校准/自动旋转修正不改。FIT/resource DT同步，原logos保留；限定属性差异、FIT哈希、内存边界、BOOT容量与Windows文件哈希检查均通过。

真机已有匹配`6.1.115-vendor-rk35xx`的gc5035/ov8858/dw9714模块，media-ctl/v4l2-ctl可用，现有motion/方向/compass/BT/USB/SDDM均active。模块由udev正常加载，未增加强制早期insmod。

## 文件与刷入

`outputs/armbian/official-f8-camera-c1/BOOT_ONLY_ARMBIAN_CAMERA_C1.img`

- 长度 **49453368** 字节。
- SHA256 **7a8d407f9aa32dee398e72f2a5539afd3f5d4fa276ca413e2e665ce9b8da4cc0**。
- RKDevTool仅勾boot，地址 **0x00008000**；不刷rootfs/Loader，不擦除。
- 先安全移除外设，拔U盘再进入Loader。启动后先联网并回复状态/IP。
- 回退：`outputs/armbian/official-f8-motion-s1/BOOT_ONLY_ARMBIAN_MOTION_S1.img`（SHA1b39e4e0…5dd682c7），仍仅刷boot。

不需要重打完整root包。`runtime-integration.json`承接当前S1 root资产，保存当前音频/USB/BT/传感器/指南针修正依赖；BOOT单文件并不安装这些root文件。

## 启动后的验收顺序

先通过固定公钥SSH运行 `tools/read-f8-camera.sh` 保存新的、不同名称的快照，确认新boot和chosen c1、摄像头实际5-0037/5-0036绑定与ID日志、camera电源、media graph、视频/subdev节点及失败单元。若任一sensor ID失败，先取证复位/时钟/供电，不用i2cdetect全总线扫描或强行写寄存器。

随后分别验证前、后摄短时帧接收；正确配置media链后再预览，明确前后选择和图像方向。ISP3A、曝光/白平衡、后摄调焦、画质和拍照保存必须逐项验收。不能盲把video0作为相机预览，RKISP还有params/stats/raw读写节点。

## 用户空间尚待处理

已安装libcamera0.7/IPA及PipeWire libcamera插件，但未有摄像头链路可枚举。RKISP3与现成libcamera pipeline是否适配未实测，不能假定安装libcamera即可用。

当前APT缓存没有rkaiq/camera-engine包。原厂暂存根仍有精确匹配的两个IQ JSON：`gc5035_XHG-RKX11F-V5_HR232H65.json`、`ov8858_HS5885-BNSM1018-V01_default.json`。原厂rkaiq用户库/服务来自5.10系统，尚未装入原生root，需核对6.1 ISP用户ABI/库依赖及IQ格式后再用，不直接复制整套Ubuntu旧库。第一阶段芯片识别/原始链路取帧与自动3A分开验收。

证据：`local/hardware/camera-before01.json`、`camera-prerequisites01.json`、`analysis/armbian/camera/dt-audit01.json`、`reference-tablet-camera.dtsi`及输出preflight。保留浏览器传感器兼容待办；充电/PD参数和CPU调频策略继续不改。
