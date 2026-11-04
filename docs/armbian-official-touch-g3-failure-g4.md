# G3 触摸失败与 G4 引脚修正（2026-10-29）

G3 的 F8AG3 日志盘已出现，37 个文件已保存至 `local/hardware/armbian-official-g3-20261029-01/`，`test-result.json` 记录逐文件哈希。用户反馈不能触摸与日志一致。

G3 加载触摸模块成功，但不代表控制器绑定成功。45.8 秒首次 I²C 测试超时（-110），随后 probe 失败，临时注册的 input 设备被撤销。TOUCH.JSON 未发现设备，事件数为零。失败发生在固件上传前。GPU 仍通过 Panthor/Mesa G610 硬件像素读回，Wayland 启停成功；日志快照没有 panic/Oops，系统 running。

原厂 I²C4 使用 m3（GPIO1_A2/A3，功能9）；G3 沿用 m0（GPIO3_A5/A6）。这是 G3 遗漏的板级配置。IRQ GPIO1_B5、reset GPIO1_B4 不变。G4 新增 m3 引脚组并把 I²C4 默认引用指向它，电气配置逐属性对照原厂。除 model 标识外，其余设备树内容完全相同。

G4 保留 G3 触摸模块、固件、官方内核、GPU 和已暂存根文件系统；不需重传 rootfs。initramfs 只更新版本/日志盘标识并补充按 KWin 进程和用户查询的 journal，以及 I²C 绑定日志。完整 FIT 四负载哈希、CPIO 差异、ARM64 shell 语法、FAT 和内存布局检查通过。静态检查不能证明触摸已修好。

- 镜像：`outputs/armbian/official-f8-touch-g4/BOOT_ONLY_ARMBIAN_26.8.1_TOUCH_G4_CANDIDATE.img`
- 大小：49471336 字节，小于原 boot 分区64MiB。
- SHA256：`f55b7e59dc5f8ea029dbf04c438c018339f35166b9907ae3fcb9ed7432ff011b`
- 预检：同目录 `preflight.json`；构建脚本 `tools/build-f8-touch-g4.py`。

## 真机短测

1. 按此前 RKDevTool 下载镜像流程，只刷 boot，起始 LBA `0x00008000`，分区大小 `0x00020000` 扇区；不擦除、不整盘刷。
2. 启动后在 Wayland 弹窗出现时尝试拖动标题栏、点击按钮、双指操作。窗口约90秒自动关闭是试验设计。
3. 启动后等4–5分钟，预期出现卷标 **F8AG4**。新日志包括 TOUCH.JSON、TOUCHLOG.TXT、INPUT.TXT、IRQ.TXT、TOUCHDRV.TXT、I2CBUS.TXT、KWINAPP.TXT、USERGFX.TXT，以及原GPU/系统日志。
4. 成功标准：控制器绑定、初始化无超时、实际触摸事件与操作反馈吻合；仅模块加载成功不算通过。

充电管理仍未适配/验证，需要充电时先恢复原 BOOT：`outputs/armbian/firstboot-diagnostic/CURRENT-BOOT-ROLLBACK-64MiB.img`。G3 日志已保存，可以回退。当前最后确认设备仍是 G3，不能假定原 Arch SSH 已在线。

## 后续硬件适配检查

`analysis/armbian/official-gpu-baseline-20261029/touch-abi/i2c-pinmux-audit.json` 比较的是 G3 与原厂。另发现 I²C3 m1、I²C5 m3、I²C6 m3 与候选默认引脚不同；G4 仅修改 I²C4，其余待相应外设适配时核对。I²C5 当前 disabled；总线 okay 不等于其下外设可用。不要直接批量启用外设或宣称已经适配。
