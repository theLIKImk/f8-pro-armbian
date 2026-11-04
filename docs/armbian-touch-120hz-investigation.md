# 120Hz 触摸试验准备检查（2026-11-03）

**当前已有 [60–120Hz整数滑块面板](armbian-touch-rate-panel.md)，用户确认应用、管理员验证、保留和恢复正常。原手动试用任务已结束；后文为时序研究历史。面板未修复高频断触，也没有自动持久化到BOOT。**

**最新已按用户要求切至128档无测试程序试用：p128-manual1，srcversion1AFFBA60D1DAFFDEAD7BE9F（此前约114.5Hz）。已停止上一轮122手动回退timer、串行确认/恢复原版，再加载128并建立新的180秒回退timer。不启动测试App或采集，未改BOOT/开机模块。证据local/hardware/touch-rate-p128-manual01.json；到期是否已回退需读p128-manual1/restore-result.json。**

**最新手动试用：用户要求再次切到122档、先不启动测试程序。已载入p122-manual1（B769C22C37A1C4330D85F05），关闭频率测试窗口，不启动采集或测试App；独立timer在加载后180秒恢复原版。当前状态可能随timer变回原版，读取该trial的restore-result.json核对，不把旧加载记录当持续生效。**

**最新：122档达到约120.1Hz但用户确认断触/乱跳，未通过。128复测已完成，约114.5Hz、20秒内77次触点释放，主观跟手反馈尚待回复，不能判稳定。已经恢复原版srcversion6A8F0920D4E483066E520A4并停止回退timer。所有试验仅在RAM中，未改BOOT/开机模块。最新细节见文末。**

用户在保留当前触摸后进一步要求“先尝试120Hz”。下方“缺少映射”部分保留为最初只读调查历史；后续已完成离线反汇编、校验验证及多档实测。

## 当前实机

只读证据 `local/hardware/touch-rate-controls01.json`：

- boot_id b12892c7-f058-460e-8018-e2be35bfc685，6.1.115-vendor-rk35xx。
- 4-0040 正常绑定 f8-gsl-shuping，event5；已加载 srcversion=6A8F0920D4E483066E520A4。
- 开机模块 SHA256仍为 bb8fd9db0bf16972e6760ca9d8ba8489e91a516c31269fc770346fe75d7a505d。
- 无触摸模块参数、无proc gsl配置接口、无sysfs report_rate/scan_rate 控制项。
- 当前设备树触摸总线feac0000及ts@40没有报告频率属性。未改模块、BOOT、固件、I2C频率或寄存器。

## 排查结论

本机保留驱动 `gsl_ts_irq` 在上升沿中断后排队工作读取0x80数据，工作结束重新启用中断。读取函数没有可直接缩短为8.33ms的轮询周期；把主机轮询改为120次/秒不能保证控制器有120组新数据，不能据此宣称采样率提升。

`gsl_point_id.c` 的512项配置为主机侧触点识别/跟踪算法；rate字段在相应上下文是坐标/权重，不是已识别的扫描频率开关。T1/T2的合并/初始识别等待参数也不等于控制器扫描周期。

同系列Silead数据手册公开了 ACTIVE_SCANDELAY、LOW_SCANDELAY、GREEN_SCANDELAY 和配套 Ctouch Configure Suite 的概念，但没有给出本机这份固件的地址/单位/校验映射。参考 [GSL3680数据手册](https://www.armdesigner.com/download/LCD_datasheet/10.1inch_LCD/GSL3680_DataSheet_Chinese_RevA2.7.pdf) 和 [GSL1680数据手册](https://dl.linux-sunxi.org/touchscreen/GSL1680.pdf)。这些资料不是本机已确认型号/面板适配的120Hz配置，不能照搬其他芯片的200Hz上限或猜一个120数值写入。

## 继续所缺条件

需要原厂本面板的Ctouch调参工程/配置格式说明，或通过离线固件分析确认扫描周期字段及其实际单位。获得可靠映射后，才制作只改扫描周期、启动失败回退当前模块的RAM试验；以算法入口/IRQ与实际新帧同时统计验证约8.33ms，不能只看浏览器事件数或补发重复帧。工作触摸、固件及BOOT保持当前版本。

工具 `tools/inspect-f8-touch-rate-controls.py` 只读取设备树/sysfs/IRQ及模块哈希，不打开I2C设备、不抓键盘。先前约67Hz证据来自R3–R5历史记录，不冒充本轮已实测120Hz。

## 离线反汇编与首次RAM试验

用户要求继续后，使用隔离目录 `local/firmware-analysis/python` 的capstone 5.0.6反汇编本机保留固件；没有安装到平板或系统Python。`tools/disassemble-f8-touch-firmware.py` 按页/偏移提取4704个32位word，SPARC big-endian反汇编位于 `analysis/armbian/touch-rate-firmware/firmware.sparc.asm`，manifest及words.json保留源SHA与地址假设。

确认的指令链：

- `0x1b9c` 调用 `0x1280`，delay slot `0x1ba0` 从参数地址 `0x374` 取值280（页6/偏移0x74）。
- `0x1280–0x1300` 将该值组合为三组采集硬件寄存器值，并写入0xff080084/88/8c；有按硬件ID和可选校准系数换算的分支。因此称为“采集时序参数候选”，不是猜测驱动轮询周期。
- `0x271c–0x27d8` 有固件/参数校验。对地址0..0x4ff和0xd00..word[0xff8]之前的word求和，再减word[0x1fc]、word[0x200]，原版结果精确为0x5a5a5a5a。修改采集参数时用0x180原校验word做对应差额补偿，不禁用/跳过校验。

`tools/build-f8-touch-rate-probe.py --period 252` 仅修改固件word0x374：280→252，并调整0x180：0x40bce5ce→0x40bce5ea。代码、主机侧算法及512项配置不变；编译后从ELF再次验证固件只有这两项差异、算法字节相同，导入CRC与已由实际内核验证的原模块一致。SHA `61efa09e02344ef0f452446fe88eb3d58aab39854d69efb0593fbafffafd66de`，srcversion E302094212AAC7FF0D33572。

## 同一boot的20秒实测对照

`capture-report-rate.py` 使用独立tracefs实例，仅启用触摸IRQ的 irq_handler_entry，非独占读取触摸event；没有抓取键盘，也不保存坐标。首次触摸自动开始20秒，等待最长180秒、服务最长210秒，结束关闭并删除自己的trace实例。普通用户Qt/Wayland蓝色测试区持续画圈。检查采集前后模块版本一致，避免回退期间混合统计。

| 配置 | 原始中断次数 | 中断间隔中位数 | 中断频率 | evdev帧数 | SYN_DROPPED |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版280 | 1355 | 14.768ms | 67.714Hz | 1347 | 0 |
| 候选252 | 1503 | 13.308ms | 75.143Hz | 1481 | 0 |

用户确认候选252触摸正常。试验在同一boot b12892c7…进行；原始IRQ和evdev一起变化，支持这个参数影响实际采集/上报时序，而不是应用补帧。这里只验了单指连续画圈，候选252有一次evdev>100ms间隔，不把它写成“完全零间隙/长期稳定”。

载入前独立调度180秒后的恢复任务，候选只存在 `/var/lib/f8-pro/touch-rate/p252-load/`；没有改开机模块/BOOT/固件默认值。读完结果已主动恢复原版 srcversion=6A8F0920D4E483066E520A4，并停止自己的回退timer。证据 `touch-rate-baseline1-result01.json`、`touch-rate-p252-load01.json`、`touch-rate-p252-result-restore01.json`。

两点线性估算为 `间隔ms≈0.168+0.052142857×参数值`。目标8.333ms对应参数约156.60；选择157的估算值为119.70Hz。该估算必须用下一轮实机IRQ/事件确认，不能先标120Hz通过。

### 后续157/128测量与122档验证

157实测95.311Hz（10.492ms，1908次IRQ/20秒），evdev中位95.283Hz、SYN_DROPPED=0、最高1点；用户确认触摸正常。说明最初两点线性外推不成立，不能标为120Hz成功。157模块SHA d391f2b7f81970b0e4ae94c476d51c2d41623296e22906ea208fb245e47d2266。读完结果已恢复原版，停止自身timer。

继续小步到128：实测114.824Hz（8.709ms，2095次IRQ/20秒），evdev中位114.587Hz，SYN_DROPPED=0，最高1点；用户确认正常。128模块SHA b7dc8cafa0ecd8f37d28d49cf11556282dfa04c3d43780c7d80e6cbe9beda58e。独立trace实例增加仅I2C读请求/传输结果的时间记录，不启用reply或保存数据载荷；44字节读取中位4.245ms、最高4.591ms。存在一次IRQ>100ms间隔和四次evdev>100ms间隔，因此这里的Hz是连续间隔的中位节奏，不等于全程平均吞吐或零断触认证。128结束也恢复原版。

基于157/128局部测量，准备122档进一步接近120Hz：固件0x374改为0x7a，0x180补偿为0x40bce66c；模块SHA bb7b4a71e3375ac40045040bcb3b5383972c7402b0ee9bafa41157ccd72355e9，srcversion B769C22C37A1C4330D85F05。首次p122-1在新窗口打开前已开始采集，启动器守卫触发回退；用户确认当时手指仍接触屏幕，不能用该轮认定误触或取得有效120Hz结果。记录未覆盖。

已改为用户在Qt界面先点“开始20秒测试”，再进入蓝色区域画圈；显示实时绿色触点/轨迹用于跟手判断，坐标只在GUI内存中绘制，不写磁盘。新轮p122-2使用独立目录、load2和独立180秒回退timer，不覆盖首轮；当前等待用户完成。本次没有改开机默认值。

证据 local/hardware/touch-rate-p157-result-restore01.json、touch-rate-p128-result-restore01.json、touch-rate-p122-load01.json、touch-rate-p122-load02.json。measurement里的device_modified=false只描述采集器本身没有设备写入；外层load记录和不同srcversion明确标识固件时序候选，不把这字段当整轮完全只读。

### 122档达到约120Hz，但连续跟踪失败

p122-2实测IRQ中位120.120Hz（8.325ms，2376次/20秒），evdev中位119.689Hz；SYN_DROPPED=0、最高1点，但出现113次触点释放转换/113个零触点帧。用户观察绿色触点后明确反馈“有断触或乱跳”。因此**只证明达到约120Hz交付节奏，稳定性验收失败，不能作为可用120Hz版本**。I2C44字节读取中位4.192ms、最高4.592ms。

立即恢复原版srcversion6A8F0920D4E483066E520A4，停止p122-2回退timer，开机模块/BOOT保持不变。证据 `local/hardware/touch-rate-p122-result-restore02.json`。

用户随后要求“再次试试128档位”。已复用原128候选（未修改参数/算法），新轮p128-2使用按钮开始+绿色触点轨迹，独立load2及180秒回退timer；目前等用户完成连续跟踪复测。128首轮没有实时轨迹，因此不能用首轮“触摸正常”的主观反馈代替这次更直接的跟手观察。

### 128复测完成与全档位触点连续性比较

p128-2结果：2293次IRQ/20秒，中位8.733ms（114.508Hz）；evdev 1997帧、中位114.416Hz；无>100ms间隔、SYN_DROPPED=0、最高1点，但出现77次触点释放转换和77个零触点帧。I2C44字节读取中位4.178ms、最高4.611ms。已读取结果并恢复原版，关闭p128-2 timer；不是把128留作当前运行配置。用户对实时绿色触点的主观反馈还未收到，不能自行写成通过。

进一步只读比较所有已保存帧：

| 参数/轮次 | 中位IRQ频率 | 触点释放转换 | 零触点帧 |
| --- | ---: | ---: | ---: |
| 原版280 | 67.714Hz | 0 | 0 |
| 252 | 75.143Hz | 0 | 0 |
| 157 | 95.311Hz | 12 | 12 |
| 128首轮 | 114.824Hz | 53 | 53 |
| 122 | 120.120Hz | 113 | 113 |
| 128复测 | 114.508Hz | 77 | 77 |

各轮都是提示单指连续画圈、20秒且SYN_DROPPED=0。若按提示持续不抬手，则这些释放属于跟踪丢点；不能只用缓冲区无丢帧或初期主观“正常”宣称95/115Hz稳定。不同操作不是严格重复的实验，不能把释放数量差异当精确改善百分比。数据支持高频采集与触点连续性存在权衡，进一步需要分析信号积分/阈值/算法时间尺度，而不是继续降低时序值或简单补发触点。

证据 `local/hardware/touch-rate-p128-result-restore02.json`、`touch-rate-release-comparison01.json`；每轮完整帧和中断时间戳仍保存在平板 `/var/lib/f8-pro/touch-rate/<round>/`。GUI坐标轨迹没有保存到磁盘。

用户随后确认调频是控制器层面全局生效，再要求“再改成122试试，先不启动测试程序”。已用 `tools/load-f8-touch-p122-manual.py` 加载相同122候选，关闭f8-touch-rate-panel.service，不调用GUI或采集器。路径 `/var/lib/f8-pro/touch-rate/p122-manual1`，独立回退timer `f8-touch-rate-rollback-p122-manual1.timer`，180秒后执行自己的restore.py。证据 `local/hardware/touch-rate-p122-manual01.json`。开机模块/BOOT保持原版；先前122断触验收失败结论仍保留，本次用于日常界面主观比较。
