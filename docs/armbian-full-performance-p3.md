# 全性能适配 P3（2026-11-02）

用户明确要求“把性能全部放开”。当前已完成本机校准分档内的CPU全频测试和面板开放，GPU 1GHz BOOT已生成；GPU需用户刷入后逐档验证。不要误报整项全部完成。

> 后续更新：用户已启动P3，GPU500–1000MHz逐档短测及1GHz30秒负载通过，配置已保存为GPU200–1000、小核按内核表至1800、大核按当次校准表且不超过2400MHz。正在进行最后一次重启恢复检查；下方初始“待刷/待测”是阶段历史。

> 最终重启恢复已通过：新boot_id `9de17bd7-c3f5-4834-8420-f4ff4de2107f`，启动40秒时只读确认GPU自动200–1000MHz、CPU P3模块已自动加载、三个policy均ondemand；两启动服务active/exited、Result success、ExecMainStatus0，无failed unit及GPU/Oops错误。此次小核上限1800、大核两组2256MHz，属于当次PVTM表的正常结果。证据 `full-performance-reboot-verify01.json`；脚本没有调用apply，因此证明是开机自动恢复。面板已在普通用户会话运行。GPU1GHz已放开，当前整项频率开放与开机恢复完成；长期全核/GPU混合负载和热触发等仍不属于已验证范围。

## P3实机验证补充

首个P3启动boot_id `33e611d7-6bdd-4c16-82aa-c17156738f73`，CPU已由延迟服务自动加载、三个CPU cooling设备正常，GPU全9档可见、启动服务按当时root清单限400MHz，GPU cooling max_state8且80°C passive绑定保留。证据gpu-p3-start01.json。

GPU500/600/700/800/900/1000MHz各3秒terrain1280×720短测返回0，每档至少6次实际SCMI目标时钟采样，分别675/675/700/750/800/850mV，最高56.384°C，无GPU fault/hang/Oops。请求1GHz下build/texture输出Validation Success，但该验证执行过快未采到活跃目标频率，不能单独以此证明“1GHz像素验证”。1GHz后续30秒terrain有59个SCMI1GHz样本、850mV、最高66.538°C，无内核错误。测试结束先恢复200–400MHz，再更新源/root清单并应用自动200–1000MHz。证据gpu-p3-frequencies02.json、gpu-p3-sustain01.json、performance-panel-gpu1000-install01.json。

初次gpu-p3-frequencies01.json因为测试程序把休眠/着色器编译期间的200MHz当作目标频率失败而停止，实际没有GPU故障；已改为只有实际渲染时SCMI与devfreq均达目标才核对该档供电，同时保留原证据。30秒terrain平均27FPS与3秒平均84FPS持续时间不同，不能直接比较成性能提升/下降；没有把30秒当成长期稳定性验收。

### 重要修正：CPU速度等级随启动校准变化

前次“这台固定grade4所以最高2256”说法不完整。bin来自OTP，但volt_sel速度分档来自每次启动PVTM测量；相邻分档可随当次校准变化。此次CPU6出现2352MHz，3秒补测实际时钟2352MHz、1000mV、最高49.923°C，无异常（cpu-p3-recalibrated-top01.json）。旧root最高2256会把2352档过滤掉并退到2208，已修正。

当前源/root型号边界为GPU1000、A551800、A762400MHz，面板和助手以该边界与内核实际available_frequencies取交集；不修改supported-hw、不制造缺失频率、不绕过PVTM。因此若大核当次表最高2256/2304/2352，就开放到相应值；只有当次原始校准表含2400才会显示2400。该边界验证的是完整厂商OPP流程和已实测最高2352，不表示本机已逐档实测到2400。面板文字已改“可选档位按本机启动校准结果开放”。

最后一次重启由tools/reboot-f8-performance-check.py调度；验证脚本tools/verify-f8-full-performance-boot.py严格只读，不调用apply，不掩盖启动服务是否实际恢复配置。期望新boot_id、两服务active/exited且Result success、CPU P3模块自动加载、GPUmax1000000000/自动、CPU全部自动及有效校准范围，无failed/Oops/GPU错误。

## CPU：完整电压/OPP流程已工作

原P2仅固定供电、最高1200MHz，不能直接扩频表到2400。新增 `armbian/power/f8-cpufreq-p3.c`，使用当前官方6.1.115内核导出的 `rockchip_init_opp_table`、OPP供电回调、PVTM/漏电分档、read-margin及标准dev_pm_opp_set_rate。板级RK3588回调来自本地Armbian/Rockchip参考源码，保留GPL，复制于 `f8-cpufreq-p3-vendor.inc`；实际工作实现仍是运行Image中的Rockchip OPP函数，未改用6.1.172 Image。参考 [Armbian内核仓库](https://github.com/armbian/linux-rockchip)。

模块 `outputs/armbian/f8-cpu-p3/f8-cpufreq-p3.ko`，SHA256 `35461712ee2e7d827163ae208ce1f3301a7b082f3a7a26d5cba5a508f55c1196`，全部导入CRC与实际官方Image一致。参数max_little_khz/max_big_khz默认1200000，首次以限制模式加载成功后，卸载并用1800000/2400000重新加载；参数给出上限，实际频率仍由OPP校准决定。

小核bin0/grade2，大核bin0/grade4（两组）。原始DT的2256/2304/2352/2400MHz第二维supported-hw分别为0x13/0x24/0x48/0x80；grade4是BIT4，命中2256，不命中2400。2400MHz为grade7可用，不把用户给出的SoC最高标称值当成此实机无条件可用值，也未放宽supported-hw或超压。

当前有效频率：小核408/600/816/1008/1200/1416/1608/1800MHz；大核另有2016/2208/2256MHz。逐档实际时钟、电压、短负载验证已完成。第一轮测试在53秒软件时限停止，最高61.923°C、并非温度到阈值或内核故障；遗漏的最后一项CPU6/2256MHz另作3秒补测通过。没有把超时轮次记为整轮通过。

小核1800MHz为925mV，大核2256MHz为1000mV，空闲408MHz为675mV；频率下降后电压也下降，供电联动已确认。完整负载长稳、休眠/热插拔、低温环境仍未验证。驱动仍创建标准cpufreq cooling设备，保留原SOC温控映射；没有关闭温控来换取跑分。

证据：cpu-p3-init01.json、cpu-p3-full-opps01.json、cpu-p3-all-frequencies01.json、cpu-p3-top01.json，均在local/hardware。重复获取同名regulator consumer产生debugfs目录已存在和device-link EEXIST提示，OPP初始化返回0，策略/供电生效；这些提示未当成Oops，也不隐去。

当前已启用ondemand：小核408–1800、大核408–2256MHz，性能面板接受f8-p3-rk-opp驱动，证据full-performance-ready01.json。CPU模块未写入modules-load；只有新P3 BOOT marker触发延迟启动服务。在旧P2A BOOT重启时服务跳过，可用面板手动启用。

## GPU：新BOOT已离线校验，仍待实机

P3镜像在CPU P2A上启用原Panthor私有OPP剩余500–1000MHz；500/600MHz675mV、700MHz700mV、800MHz750mV、900MHz800mV、1000MHz850mV，未超出原GPU regulator约束。原P1 GPU80°C passive/5°C回差及soc温控映射保持。

`outputs/armbian/f8-gpu-p3/BOOT_ONLY_F8_ARMBIAN_FULL_PERF_P3.img`，49,460,108字节，SHA256 `cbd14e32ef05d9571745ba8b790c694f7a81112e37783a4cf873c7d0c918ef46`。官方Image、ramdisk、CPU启动参数、相机/USB/触摸等节点保持；FIT与resource DT一致、所有hash及内存范围/容量检查、Windows全量读回通过。只刷boot0x8000，回退P2A。

GPU高档在当前内核DT里禁用，不能只改面板JSON获得1GHz。因此需要这个BOOT；没有热重绑GPU/CIF或改驱动内存结构。当前GPU已验证清单仍400MHz，面板也仍只列到400，不伪装已放开1GHz。

## 已安装的启动策略与下一步

新增performance-startup.py及两个root oneshot服务，已加入f8-desktop.target；systemd-analyze verify通过。严格检查GPU marker为p3-1000mhz，否则全部跳过，P2A回退不自动加载新CPU模块。

1. GPU服务Before=sddm，在root清单范围内设自动调频和最高档，首次仍400MHz。
2. CPU服务After=SDDM/SSH/硬件准备，延迟12秒，用已校验P3模块和完整目标参数启用CPU自动调频。
3. 用户刷入并启动后，先检查marker、GPU全部档位及400MHz启动上限、CPU自动加载/温控/SSH，不能立即记全性能通过。
4. 按500/600/700/800/900/1000MHz依次短测GPU，核对实际时钟/电压/温度/错误，并保留超时/回退。
5. 成功后才将root和源performance-limits.json的GPU验证上限改1000，恢复自动、复核面板，再做适当长稳/冷启动验证。

新startup脚本、服务、P3模块、面板及root清单已同步到根fs配置脚本；尚未重建干净完整ROOTFS。CPU模块原始代码及vendor include须一起保留。P2/P2A资产用于回退，不要复用旧限频固化脚本覆盖当前配置。
