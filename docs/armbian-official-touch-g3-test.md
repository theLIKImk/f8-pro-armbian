# G3：F8 触摸与 Wayland 短测

2026-10-29。沿用已真机通过的G2官方Armbian内核、GPU域供电、Panthor/Mesa、200MHz档位和1200×1920内屏。仅启用i2c4/0x40的F8触摸匹配，GPIO/复位/pinctrl不改；model更新G3。其他设备树属性与G2完全相同。

## 候选文件

outputs/armbian/official-f8-touch-g3/BOOT_ONLY_ARMBIAN_26.8.1_TOUCH_G3_CANDIDATE.img

49471132字节，SHA256 **3797899c1444efde96c1c64e4c4ee618fa4e4f8f67de83a0ae6f4b67d1155b7b**。

2.15GB官方根镜像沿用设备现有文件，不必重传。触摸模块、事件记录工具、限时测试脚本和更新的3个单元由initramfs安装到RAM upper，不修改原Arch或冻结SquashFS。

## 已完成的离线核验

- F8专用模块完整链接，48项导入CRC（含module_layout）与实际官方26.8.1模块匹配；vermagic匹配6.1.115，未绕过版本检查。
- 原厂r8/shuping固件/配置在完整模块中逐字节正确；新/官方/原厂算法版本0x20140421一致，但未当作全部算法等价证明。
- 专用驱动名和OF匹配避免内置通用GSL重复注册，算法独立链接不共享全局状态。参考原厂probe的静态指令证实IRQ rising，与候选一致。
- DT差异只包括触摸compatible/status及model，G2 GPU域修正/电压/时序不改；shell、FAT、cpio、FIT四payload与12KiB pad布局通过。
- 新单元超时/日志字段验证，事件工具在隔离ARM64根中无触摸设备时明确报错。尚未加载触摸模块或向控制器上传固件。

## 测试步骤

1. 沿用只刷boot的方法，起始0x00008000、大小0x00020000扇区，选择G3，不改其他分区。
2. 启动后将尝试加载F8触摸模块并上传本机专用固件，随后沿用严格GPU像素读回；GPU通过才启动Wayland测试窗口。
3. 窗口保留约90秒。先尝试用手指拖动标题栏、点击按钮；可以在窗口外空白区域轻触四角、两三指按下用于记录触点，空白处没有专门画图反馈。最后点OK可提前关闭，90秒后自动关闭也属预期。
4. 等待约4–5分钟，Windows应出现 **F8AG3** 日志盘。通知助手盘符，并说明是否能点击、拖动、是否反向/偏移、能否多点。即使触摸无反应，也应采集日志。
5. 记录工具只读取名为f8-gsl-shuping的触摸event，不抓取设备、不读取键盘，因此KWin仍能同时接收事件。记录约110秒，输出TOUCH.JSON的轴范围、事件/释放/多点计数与有限样本；INPUT.TXT、IRQ.TXT、TOUCHDRV.TXT提供绑定与IRQ证据。

本轮把KWin标准输出/错误明确送入journal，KWIN.TXT保留头尾，RENDER.TXT提取renderer/GL/输入线索，补齐G2缺少compositor自身renderer日志的限制。报告timer约210秒导出，避免在触摸试验尚未结束时取快照。

## 边界与回退

触摸尚未真机验收，不将ABI/版本检查当作固件、IRQ、坐标或多点通过。原始坐标800×1280，物理显示1200×1920，实际映射和方向需要这轮操作确认。休眠/旋转/自动键盘/完整Plasma/SDDM仍未验收。

充电仍未适配：需要充电时先只刷回原BOOT，再接充电器。原Arch分区仍只读充当镜像容器，目标写入都在RAM。日志保全后可回退outputs/armbian/firstboot-diagnostic/CURRENT-BOOT-ROLLBACK-64MiB.img。

G2已测基线、所有旧日志和G3源文件分别保留。当前没有自动刷机、硬件触摸结果或后台任务。
