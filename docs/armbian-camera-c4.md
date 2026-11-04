> **2026-11-01 C4真机已启动、双摄取帧通过，3A未通过：**最新见[实测结果](armbian-camera-c4-result.md)。boot532eb6df/192.0.2.227；提前加载3.2/3.7秒，sensor完整接入media/ISP。后摄8帧NV12；前RAW2帧，增加blanking后前ISP12帧；实际画面偏暗、前摄倒置待校正。C4可保留，无需再刷。blanking前80/后64已按C4守卫持久化并手动验证，新camera-start SHA791d0bcf…7ff2a20，开机自动应用/初次ISP免RAW预热待验。隔离AIQ双摄程序用户态崩溃已禁用，前IQ为ISP21不适配ISP30；后独立AIQ仅2帧超时，未成功，无自启动/常驻，试验全局IQ链接已移除。未内核Oops、0failed，未重启/热重绑；后续解决ISP30 IQ/UAPI/3A及方向。

# 摄像头C4：保留等待链、提前加载sensor（2026-11-01）

## 本轮实机只读确认

SSH 192.0.2.227 / f8test，boot仍为`6b50d20b-56e6-48b9-834e-b8ebb3260b31`，不是发生C1 Oops的旧boot。systemd running、0failed，tainted=4096；不能仅凭服务正常证明相机可用。

新证据：`local/hardware/camera-c2-resume-read01.json`、`camera-c2-resume-async01.json`、`camera-c2-resume-async02.json`。均只读，无unbind/rebind、模块重载、图修改或取帧。

- C2两颗sensor正常绑定，media图的DPHY输入没有sensor链。
- pending显示sensor已注册但未归属，DPHY等notifier标题下等待项为空；ISP仍等sditf。这更符合匹配项已被清理，不能称为所有notifier还在互相等待。
- dmesg在2.6665/2.6705秒分别清理两个CIF的1个未就绪subdev，紧接着notifier completed；sensor在7.29–7.38秒才probe/识别。
- 当前boot的GC5035还曾在756秒重新probe，说明前一位AI有过后续操作；本轮没有重复重载。
- 实机存在`rkcif_clr_unready_dev`和`rkisp_clr_unready_dev`符号，地址与本地System.map对应。
- 两颗官方sensor模块的`modprobe --show-depends`只列各自模块；root的`/usr/sbin/modprobe`存在。C2原有camera-start脚本及unit哈希仍与已记录版本一致。

## 源码与实际二进制交叉核对

从[Armbian官方linux-rockchip仓库](https://github.com/armbian/linux-rockchip/tree/372ce582b94a3360a29727c3c49c88bb7509da22)下载固定commit的6.1.115 Makefile、CIF/ISP dev.c和v4l2-async.c，保存于`analysis/armbian/camera/c4/`。这是同版本参考，**尚未证明它就是官方26.8.1 Image的精确构建commit**，不据此重编内核。

[v4l2-async.c](https://github.com/armbian/linux-rockchip/blob/372ce582b94a3360a29727c3c49c88bb7509da22/drivers/media/v4l2-core/v4l2-async.c)中的清理函数递归进入已绑定子notifier，再移除waiting项。CIF late_initcall调用该清理并尝试注册sditf；ISP还有late_initcall_sync清理。CIF另有等待notifier最多5秒的线程，故只把模块放在systemd后期加载仍可能错过sditf注册窗口。

对**实际C2 Image**使用匹配符号地址反汇编，确认CIF/ISP入口确实调用`v4l2_async_notifier_clr_unready_dev`，其递归函数确实移除链表项并清零对应字段。三份反汇编记录也保存于上述目录。这支持冷启动时跳过清理的试验，不代表取帧已成功。

另发现`official-kernel/boot/vmlinuz`文件哈希与C2内核不同，不能直接替换。C4完全从已运行C2镜像提取内核，固定SHA256为`a67daf71caefef6b97a22ba708bbb302b239a4a9b4874cadd17a217ebd0c37b7`、46561792字节；没有从任何源码树或同名包替换Image。

## C4修改与检查

1. 将原有单个启动参数扩展为`initcall_blacklist=rockchip_cpufreq_driver_init,rkcif_clr_unready_dev,rkisp_clr_unready_dev`，CPU原黑名单和`cpufreq.off=1`保留。
2. 新增chosen `f8-camera-async-trial=c4`。原`f8-camera-trial=c2`故意保留，使已装root服务继续工作。
3. 在initramfs已经挂载并校验root、移动dev/proc/sys/run之后、启动systemd之前，通过busybox chroot加载root中既有官方gc5035/ov8858模块，每项最多8秒，失败记日志并继续桌面流程，原服务仍可重试。没有写root配置或自动取帧。

DT硬件资源、端点、供电、共享MCLK、VCM禁用及USB/BT/S1标记保持C2；FIT与resource内DT同步。RAM包逐记录核对仅init正文改变；ARM64 BusyBox实际语法解析及timeout/chroot applet检查通过。FIT属性/哈希、固定官方内核、内存与分区容量、Windows独立SHA和刷入检查器均通过。

构建脚本：`tools/build-f8-camera-c4.py`；增量init源码：`armbian/camera/early-sensors-c4.sh`；报告：`outputs/armbian/official-f8-camera-c4/preflight.json`。C4未冷启动、未取帧。

## 文件与刷入

`D:\Netdisk\杂项\F8-PRO\archlinux\outputs\armbian\official-f8-camera-c4\BOOT_ONLY_ARMBIAN_CAMERA_C4.img`

- 49453800字节。
- SHA256：`fbbfa1ece55b3c62decbd10ae9c2ac98ed5d717dd5f8b941c49004deb6c0903a`。
- 进入Loader，仅选boot / LBA `0x00008000`；不写Loader/rootfs、不擦除。C3禁止刷。
- 测试基线回退为C2；更早已验收基线为S1。均只刷BOOT，不重复root打包或传输。
- 用户确认C4启动后，再通过SSH记录新boot，执行`tools/read-f8-camera-c4-boot.sh`，输出到新证据文件。

先确认实际cmdline包含三项黑名单、内核日志有C4 early加载、没有清理未就绪项、sensor进入media图、sditf接到ISP。若链路完整，再选正确节点进行限时取帧。实际sensor加载能否赶上5秒窗口、两个ISP晚initial probe能否接完整图，都必须冷启动实测，不因离线通过而默认成功。

CIF/DPHY热重绑仍禁止。保持其他硬件root配置、个人指南针校准、充电/PD暂缓和CPU保守策略。本轮无平板写入、刷写或重启，无后台任务。
