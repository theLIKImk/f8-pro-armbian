# F8 闪光灯 F1（2026-11-03）

**当前已升级F2：亮度、常亮、循环闪烁与关窗熄灭均获用户实测通过。F1内容保留为历史/回退依据；当前实现和限制请读 [F2交接](armbian-flash-f2.md)。**

已完成后置闪光灯的固定短闪、自动熄灭、标准 LED 接口和图形控制。用户两次确认灯短亮后正常熄灭，第二次通过“F8 闪光灯”界面及管理员验证触发。开机加载已配置，尚未重启验收；拍照曝光同步、持续补光与电流/亮度调节未实现。

## 原厂接线与当前基线

只读原厂 `vendor/ubuntu-5.10.160/boot-assets/board.dtb`：

- `/flash-rgb13h`，compatible=`led,rgb13h`，label=`gpio-flash`。
- `enable-gpio` 指向 `/pinctrl/gpio@fec40000`，gpio3 offset17，即 GPIO3_C1，全局编号113，active-high。
- 振动马达为相邻 GPIO3_C2（114），不复用该引脚。
- 原厂标注 led-max-microamp=20000、flash-max-microamp=20000、flash-max-timeout-us=1000000。这些 DT 数字不等于已经测得的实际电流。
- OV8858 的 `flash-leds` 指向该节点。当前移植摄像头 DT 当初有意略过此引用及闪光灯节点。

实际 boot_id=`b12892c7-f058-460e-8018-e2be35bfc685`、内核 `6.1.115-vendor-rk35xx`。适配前 pin113 的 MUX/GPIO 均未占用，只有存储指示 LED；CONFIG_LEDS_GPIO=y、CONFIG_LEDS_CLASS_FLASH 未启用，无 rgb13h 模块。

本地配套内核源有 `drivers/leds/leds-rgb13h.c`。其 GPIO 分支仅按开关输出，不改变 GPIO 驱动电流；也可参看 [Rockchip 上游实现](https://github.com/rockchip-linux/kernel/blob/develop-6.1/drivers/leds/leds-rgb13h.c)。本次不照搬需额外 LED flash class/V4L2 支持的整套驱动。

## F1 实现

`armbian/camera/f8-flash.c` 是独立 GPL 模块，通过板级 GPIO lookup 申请 gpio3/17，创建标准 `/sys/class/leds/f8:white:flash`。

- 仅匹配 model 以 F8-PRO 开头的机器；申请引脚失败即退出，不抢占已有消费者。
- 上电、加载、重载、休眠、卸载及关机默认熄灭。
- max_brightness=1，只代表开关，不伪造亮度或电流档位。
- 每次亮约500ms后由内核 delayed_work 自动关闭；重复写1不延长当前脉冲，关闭后500ms冷却。
- 不使用 PWM，不接触GPIO114，不重绑摄像头/ISP，不改BOOT、分区或供电参数。

`tools/build-f8-flash.py` 使用已有匹配内核头文件交叉编译，所有导入CRC均与实际官方Image导出核对通过。模块 vermagic=`6.1.115-vendor-rk35xx SMP mod_unload modversions aarch64`；SHA256=`32cc2bc830372bea259164cce21e0e747bbd5fa6f81501817f6654a7cfa618c8`。

运行时测试读到亮1，约0.6秒时已恢复0；最终 GPIO113 out lo、GPIO114 motor仍out lo。用户确认后置灯短亮并自行熄灭。普通 rmmod/modprobe 往返通过，重载亮度0；这不能替代冷启动验收。

## 安装与使用

- 模块：`/usr/lib/modules/6.1.115-vendor-rk35xx/extra/f8-pro/f8-flash.ko`。
- 开机配置：`/etc/modules-load.d/f8-flash.conf`；已 depmod，modprobe 可解析并实际重载。
- 界面：应用菜单“F8 闪光灯”，`/usr/libexec/f8-pro/flash-panel.py`，PyQt6/Wayland。
- 固定助手：`/usr/libexec/f8-pro/flash-control.py pulse|off`，经 pkexec + `org.f8pro.flash.control` 验证；只写本机固定 LED 路径，不接受任意文件/时长/引脚。
- policy：`/usr/share/polkit-1/actions/org.f8pro.flash.policy`，active session 需管理员认证并短时缓存。非特权直接调用助手按预期拒绝，不放开sysfs写权限。

用户已确认图形短闪、管理员验证及自动熄灭正常。暂未为相机应用自动触发闪光，不能声称已经完成快门同步或浏览器闪光控制。下一步如要相机补光，应先确定曝光时序/拍照流程；不要将500ms异步手动脉冲称为硬件同步闪光。

## 文件、复现和回退

源及工具：`armbian/camera/f8-flash.c`、`flash-panel.py`、`flash-control.py`、`org.f8pro.flash.policy`、`f8-flash.desktop`；`tools/build-f8-flash.py`、`prepare-f8-flash-test.py`、`prepare-f8-flash-install.py`、`verify-f8-flash.py`。

成品：`outputs/armbian/f8-flash-f1/`。对应文件也已放入 `armbian/rootfs-overlay`，供后续ROOTFS构建集成；尚未重新打完整刷机镜像。测试时的独立副本 `/usr/local/lib/f8-pro/experimental/f8-flash-f1.ko` 保留用于追溯，开机加载实际使用标准 modules 目录中的文件。

回退时先以管理员运行 `flash-control.py off`，删除 `/etc/modules-load.d/f8-flash.conf`，再 `modprobe -r f8-flash`。需要完整移除时再删除上列模块/助手/界面/policy及desktop文件并depmod；不刷BOOT、不触碰其他硬件模块。

证据：`local/hardware/flash-before01.json`、`flash-f1-test01.json`、`flash-f1-install01.json`、`flash-f1-verify01.json`；构建 `module-check.json`、`installation-manifest.json`。未来重启后需确认LED出现且默认0，才能把cold_boot_verified置true。
