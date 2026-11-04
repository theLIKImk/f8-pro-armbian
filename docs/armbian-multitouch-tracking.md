# 五点触摸连续跟踪排查（进行中）

2026-11-02。当前 Armbian vendor 6.1.115 / KDE Wayland / libkwin6 6.6.6。

用户确认能看到五点，但多指移动不跟手、容易断；单指正常。数量与连续跟踪分开验收，目前尚未通过连续跟踪验收。

## 已知证据

- `/dev/input/event5`，f8-gsl-shuping，11 slots（驱动ID1–10），X800/Y1280，Qt设备 maximumPoints=10。
- Qt应用最高5点、五点保持3.68秒，累计TouchCancel12次。数量确认不能证明无断触。
- 80秒有界、非独占的触摸屏原始事件采集：读取时721帧，44次按下/释放，SYN_DROPPED=0。样本保留有限，不据此直接认定驱动正常或异常。
- 活跃模块SHA256 bb8fd9db0bf16972e6760ca9d8ba8489e91a516c31269fc770346fe75d7a505d，与保留的官方6.1.115触摸模块一致。

## KWin线索与待验证项

[官方v6.6.6 input.cpp](https://github.com/KDE/kwin/blob/v6.6.6/src/input.cpp)：GlobalShortcutFilter::touchDown，连续落指间隔<=250ms且距离接近时，第3个触点触发touchCancel，之后吞掉运动直到手指抬完。触屏过滤没有globalShortcutsDisabled动态检查；仅取消系统手势动作不一定阻止吞事件。

下一轮每隔1秒放下一根手指，五指齐后移动10秒，与同时落指对照。如果只有依次落指稳定，可以确认桌面手势干扰；若依次落指仍不稳，再对照同一时段原始ID/运动轨迹排查驱动。

尚未修改KWin库或配置、内核、触摸固件和BOOT。未安装KWin构建依赖。不能直接复用旧Arch KWin6.7.5构建。Ubuntu当前库为4:6.6.6-0ubuntu0.1，可从ports.ubuntu.com pool/universe/k/kwin获取匹配源；WSL kwin-touch-audit有只读审计源文件与dsc。

测试程序：armbian/touch/multitouch-test.py；安装tools/prepare-f8-multitouch-test.py。只读取自身Qt触摸事件，缓存用户私有，不合成输入、不读取键盘。

## 本次暂停交接（2026-11-02，最新优先）

用户要求先记录，额度将尽。当前未修复多指跟踪，不要宣称五点适配完成。

### 最新实测与结论

1. 用户完成单指画圈和五指移动：**单指正常，只有多指不跟手/断触**。
2. 为区分KWin手势接管，重开测试App，要求每隔约1秒逐根落指、已落指不抬起，五指齐后移动10秒。用户回复：**仍然不跟手或断触**。
3. 最新读取 `local/hardware/multitouch-results02.json`：Qt最高5点、五点保持4.68秒、1731帧、TouchCancel16次，Wayland，设备maximumPoints=10，当前已全部抬起。此数据是本轮窗口累计值，不能把所有取消都精确归因于逐根落指那一次操作。
4. 因此KWin第三指接管是已确认的源码行为，但**不足以解释全部异常，尚未确认它是此次全部断触的根因**。不能只关闭手势就视为解决，也不能据此直接认定内核驱动有缺陷。
5. App结果已改名 `five_contact_count_passed`，明确 `movement_acceptance=requires_user_test`，界面提示数量通过不等于连续跟踪通过，并显示系统取消次数。

### 下一步应做

- 改进有界、非独占触摸屏采集：保留整段帧或足够长的环形缓冲、逐帧时间戳、活动slot/tracking ID/X/Y、按下释放转换，而不是只保留最初200帧及末尾10帧。
- 与App同一时间段对照，分别采集单指、双指、逐根五指、同时五指的短测试。特别检查五指保持移动时原始触点数是否下降、ID是否跳变/被重新分配、坐标是否冻结或跳跃；统计帧间隔与SYN_DROPPED。
- 若原始事件稳定而App出现取消，再单独处理KWin过滤；若原始事件也异常，再调查GSL多点算法/驱动报告路径。当前源 `armbian/touch/official-6.1.115-f8/f8_gsl_driver.c`：gsl_ts_worker读44字节，经gsl_alg_id_main后按ID1–10上报type-B slot；record_point按ID平滑；缺失ID释放。先留证据再改，不盲改固件或重编BOOT。
- 现有原始捕获仅曾运行有界80秒，不是持续监控；本轮未重新启动捕获。新复现需要先准备采集，再提示用户操作，避免缺失同一时间段数据。

### 本轮改动/未做事项

- 已更新并重新打开 `/usr/local/lib/f8-pro/multitouch-test.py`，用户服务 `f8-multitouch-test.service`；生成器 `tools/prepare-f8-multitouch-test.py`，安装结果 `local/hardware/multitouch-install02.json`。
- 只读审计工具 `tools/inspect-f8-kwin-touch.py`、`tools/inspect-f8-kwin-build.py`，结果 `local/hardware/kwin-touch-inspect01.json`、`kwin-build-inspect01.json`。
- 平板 libkwin6/kwin-common 4:6.6.6-0ubuntu0.1；kwin-wayland程序包仍6.6.5，不能假定所有KWin包版本相同。当前没有安装kwin-dev/qt6-base-dev/cmake构建环境；以实机查询为准。
- 未修改KWin库/配置、触摸内核模块、触摸固件、BOOT或分区；未重启系统；未安装KWin构建依赖；未新建完整ROOTFS包。性能P3、KDE监视器K1和其他已验收功能保持当前状态。电池继续按用户要求跳过。
- 最新连接仍 `ssh likimk@192.0.2.227`。既有工具 `tools/ssh-f8-new-user.py` 接收stdin凭据；不要把密码写进记录/脚本/命令行。SSH指纹与既有隔离known_hosts见该工具及早前记录。

## 继续适配：同步取证与T1/T2运行时试验（2026-11-02，最新）

### 同步采集定位

R2由App按钮触发65秒同步诊断。采集touchscreen专用event5，不独占、不读键盘；完整保留每帧slot/ID/坐标、按下释放和Qt事件，时钟统一CLOCK_MONOTONIC。

- 用户：**双指正常，五指异常；触摸位置靠近更容易异常**。
- R2 1699帧、64次按下/59次释放、SYN_DROPPED=0，最高5点。
- 单指及双指阶段Qt取消0、无大幅跳跃；逐根五指阶段Qt取消0，但原始evdev已经发生触点释放/重新按下及点数下降。因此此次有驱动/算法阶段问题，不能只修改KWin。
- 后续用户补充：四指相隔2–3厘米、每次按压几百毫秒快速敲击也丢点。

R3增加独立tracefs实例和暂时kprobe，仅在 `f8_gsl_shuping:gsl_alg_id_main` 入口读取cinfo输入（count及X/Y/ID10组），不写算法状态/控制器。与evdev同步采集35秒，完成即删除自己的probe和instance；等待用户点击最多300秒，总服务上限380秒。探针命令用os.open O_WRONLY、不使用O_TRUNC，避免清除其他探针。首次用Python append打开tracefs失败，未产生探针，已修；一次stop已退出的App返回5已做幂等处理。不要因此重跑旧R3目录覆盖证据。

R3 1476条原始算法输入，trace1476/1476无缓冲丢失；393个evdev帧。离线用原保留GSL C源码/512项配置回放，393/393帧最终触点数量与实机匹配（匹配时差<10ms，过滤同驱动坐标边界），见multitouch-r3-replay-validation.json。**不是完整坐标/硬件等价证明**。

### T1：缩小近点合并范围

原算法conf[0x18]=0，PointRepeat回退32/96，丢点后8帧扩大合并区。R3同一批输入原设置有158帧被此步骤减少触点；16/24阈值回放该步骤不再合并。

T1仅conf[0x18]改为0x00100018，驱动/算法源码、控制器固件不变。模块91680字节，SHA8910fe6644870cfa190d44d0915094e859243f6284d069e8fd8baabadf99add2；实际加载srcversion7962C079BE17084910E2C36。用原6.1.115 headers构建，导入CRC与已由官方实际模块验证的原模块逐项相同；固件逐字节一致，512配置只有1项差异。

通过单独有界systemd加载器rmmod（无force）/insmod热换触摸模块，失败自动尝试回退原模块。已审查remove关闭IRQ/notifier并同步取消work；**不是相机CIF/DPHY热重绑**。摄像头仍禁止热重绑。

用户T1反馈：**有改善，但仍丢点**，未验收通过。R4 1189条算法输入、597帧、54次按下/51释放，丢帧0；完整数据保留。对R4同一输入回放，T1 4->4为218帧、5->5为181帧。

### T2：降低多指新点的首次识别等待（当前加载，等待用户验收）

在T1基础上仅conf[0x28]由0x1b6db688改成0x09249248：原按触点数1–10延迟[0,1,2,3,3,3,3,3,3,3]帧，改[0,1,1,1,1,1,1,1,1,1]。单指/双指不变。未添加延迟释放/虚构触点，未关闭整帧over_report保护。

R4同一原始输入离线回放，T2 4->4为258帧、5->5为213帧；仅作为算法比较，不能视为不同用户操作的实测改善百分比。关闭整帧mask只额外改善1帧，故**未部署该候选**。继续保留global flags0x40000d01。

T2：outputs/armbian/f8-touch-tracking-t2/f8_gsl_shuping.ko，SHA4acdec3aabc2c1d95fa30f89fc014524c9a1d54b4bd14748380c1ad55a8c1092，91680字节，srcversionFBA0207B7B63A97F716A215。同样ABI逐项一致、固件不变、仅512配置第0x18和0x28变化。构建tools/build-f8-touch-tracking-t1.py --profile t2，源码副本/清单在各outputs目录。

当前运行时T2已加载，event5/I2C绑定成功。原BOOT、/usr/libexec/f8-pro/f8_gsl_shuping.ko（bb8fd9db…）、开机helper均未改。**重启会回到旧模块，不声称持久化完成。** T1/T2候选放在/usr/local/lib/f8-pro/experimental。T2加载器失败回退T1；root结果/var/lib/f8-pro/touch-t2/load-result.json，T1同级touch-t1。已加载候选只用于当前运行时试验，未创建新BOOT。

当前R5窗口（35秒）等待/进行T2四指快速敲击+五指靠近验收，用户问题已发送。读tools/read-f8-tracking-r5.py（若尚不存在，用R3 reader按固定r3->r5派生），或按R4 reader方式取/var/lib/f8-pro/touch-diagnostic/r5完整trace。**下一步先读取并记录用户T2反馈，不能当成通过。** 若快速三指以上Qt收到TouchCancel，KWin全局触屏手势仍可能同时拦截；算法修正不等于关闭KWin手势。若算法入口原始点数也已减少，仍需进一步排查控制器侧，不能凭软件输出恢复不存在的原始点。

### 资产与工具

- armbian/touch/capture-tracking.py、capture-algorithm.py、load-tracking-t1.py、load-tracking-t2.py、multitouch-test.py。
- tools/prepare-f8-tracking-r2.py、prepare-f8-tracking-r3.py --round r3/r4/r5、read-f8-tracking-r2.py/read-f8-tracking-r3.py/read-f8-tracking-r4.py。
- tools/replay-f8-touch-algorithm.py（WSL gcc+ctypes离线，不触硬件），analyze-f8-tracking-r2.py，build-f8-touch-tracking-t1.py --profile t1/t2。
- local/hardware/multitouch-r2-trace02.json及-analysis、multitouch-r3-trace01.json及-replay/-replay-validation、multitouch-r4-trace01.json及-replay、multitouch-t1-load01.json、multitouch-t2-load01.json、multitouch-r5-ready01.json。
- 离线回放临时目录/var/tmp/f8-pro-armbian/touch-replay-r3会按最新输入覆盖临时outputs；以保存的原始trace和各输入-replay.json为证据，必要时重新回放，不误把R4临时输出当R3。

USB当前已恢复验收；本轮未改USB/充电/性能/BOOT/分区，未重启。触摸未整体验收通过。

## 转入Phira ARM64构建前的最新状态

用户T2反馈：**比之前好，但仍丢点**。R5已完成459帧、355次按下/352释放、丢帧0，完整记录local/hardware/multitouch-r5-trace01.json；临时探针已全部清理。四指快敲阶段控制器原始数据有156条四点包，evdev有58帧四点，Qt TouchCancel18次；五指靠近阶段原始数据最高4点，Qt取消0。两层问题均未解决，不能宣称T2完成适配。

用户澄清“其他平板/手机可以更近”指其他设备，并未在这台F8原厂安卓测过，不据此推断F8硬件极限或原厂表现。

已读取本地D:/Netdisk/杂项/F8-PRO/update-ANDROID12.img（只读，未刷机）。Android5.10.110内核SHA1c3c356a07ba239842ab8914633f4ca56a91d315e1b7e4d6304e1227d2682d32；包含移植基线完整38808字节固件（60a271f6…206809）及2048字节原配置（032de666…643b8），两者均逐字节匹配，DT同为gslX680_shuping。当前T2配置有2项试验变更，不能把“基线一致”写成“T2全部一致”。Android实际启动/近指表现未测，完整驱动算法实现等价未证。见tools/inspect-f8-android-touch.py和analysis/armbian/android-touch-20261102/comparison.json及只读提取Image。

KWin触屏接管修正K2正在独立构建尝试：armbian/touch/build-kwin-touch-k2.py，平板/var/tmp/f8-pro-kwin-touch-k2，systemd f8-kwin-touch-build。只下载提取206个依赖，未apt安装/升级（系统Mesa被固定，apt satisfy模拟无法满足，未强行升级）。原生源码为Ubuntu4:6.6.6-0ubuntu0.1，两源归档SHA已核对，应用Ubuntu两补丁；拟加[Touchscreen]GlobalSwipeGestures=false时跳过全局触屏手势，保留键盘/触控板。**尚未安装KWin修正或改kwinrc，也未重启桌面**。构建先失败于虚拟Qt ABI依赖，已支持provider；HTTP批量下载超时，改TLS并发+SHA校验；旧apt下载的epoch转义名残留损坏deb导致提取失败，已只提取selected候选校验过的文件，deps-extracted标记防止镜像链接后重复解包。最新已用local/hardware/kwin-touch-build-resume03.json重启尝试，需tools/read-f8-kwin-touch-build.py确认状态，不盲重复构建或替换系统库。当前桌面仍原版KWin，触摸RAM中仍T2；原BOOT/开机模块/USB配置未改。

用户新要求：把https://github.com/TeamFlos/phira/编译ARM64。当前按Armbian Linux ARM64目标推进，源games/phira固定750579396cbc5dc61e6379fbfb2aa1adb70751a6（0.8.2），构建脚本tools/build-phira-arm64.py，WSL工作/var/tmp/f8-pro-phira-arm64。Phira任务优先，触摸阶段保留，尚未验收/持久化。

## 2026-11-03：用户保留当前触摸与上报率查询

用户要求“目前触摸也保留”，按当前实机状态保留，暂不推进触摸/KWin调整。本轮仅离线分析已留存的R3/R4/R5记录，没有加载触摸模块、改配置或固件。前述T2运行时状态属于历史boot；本轮没有把它重新加载或持久化，不能据历史记录声称新boot仍在T2。

`tools/analyze-f8-touch-rate.py` 从完整算法入口探针时间戳及evdev帧时间戳离线分析，结果 `local/hardware/multitouch-report-rate-analysis01.json`，各原始记录SHA一并保存：

- 算法入口的快速间隔簇（13.5–17ms）在R3/R4/R5分别有955/319/813个间隔，中位数14.798/14.851/14.825ms，即67.58/67.34/67.45Hz。
- 该数据证明现有固件/链路曾有约67Hz的快速交付节奏，不是控制器内部电极扫描率测量，也不是经过持续移动测试认证的硬件最高上限。
- evdev排除>=100ms间隔后中位间隔约29.64/29.65/29.86ms；不少帧约30ms才更新，不能用它与记录总时长的简单平均定义扫描率。动作、过滤、丢点和上层交付均可能改变观测结果，本轮未分别归因。
- 驱动使用IRQ触发工作队列读取控制器，不是可直接改成120/240Hz的固定周期轮询。尚无本机准确控制器/面板扫描率规格或已验证的调频配置，理论上限保持未知。

查询到的其他GSL1680/3680资料不能直接当作本机硬件最高规格；本次不据此宣称支持120/200/240Hz，也未写入试验频率。
