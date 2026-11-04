# Linux 问题修复，2026-11-02

> 最终：麦克风普通应用验收与管理员认证修复通过；全性能P3 GPU200–1000MHz逐档/30秒负载通过，CPU采用完整OPP并按每次PVTM校准表开放（型号边界A551800/A762400MHz），重启后的自动恢复已只读核验。此次大核2256MHz、前次2352MHz均实际验证过，不能将分档说成固定熔丝上限。详 [P3完整记录](armbian-full-performance-p3.md)。

> 最新全性能进展：CPU完整OPP/电压联动已工作，小核1.8GHz、大核2.256GHz按实机grade4开放并短测通过；GPU1GHz候选待刷入验证。性能面板和root启动资源已同步。详 [全性能P3](armbian-full-performance-p3.md)。

> 最新：CPU P2A已启动、独立模块手动加载及三集群816/1008/1200MHz短测通过，自动调频已启用；“F8 性能控制”已安装并经用户确认触摸/认证/固定与恢复正常。最高额定频率和完整DVFS仍待适配，模块不自动加载。详 [性能控制面板与P2A记录](armbian-performance-panel.md)。下方保留此前阶段记录，旧“待启动/待加载”由本条更新。

当前用户 likimk / 192.0.2.227，UID1602，官方 6.1.115 vendor Image，KDE Wayland。测试密码不写入文档。旧构建已清理，历史路径不保证存在。

## 管理员认证：已实机通过

安装软件、修改系统设置时密码窗口闪退。日志明确提示 polkit-agent-helper-1 必须 setuid root；实际权限不正确。恢复 `/usr/lib/polkit-1/polkit-agent-helper-1` 为 root:root 4755，添加 dpkg-statoverride 保持包更新后的权限，并 mask 当前 vendor 内核不适配的 socket helper，使用 Polkit 正常的 setuid 密码认证。没有放行全部管理员操作或绕过密码。

用户确认：“窗口正常，验证通过”。修改前后元数据在平板 `/var/lib/f8-pro/polkit-compat-20261102/`，执行工具 `tools/fix-f8-polkit-and-ssh.py`，证据 `local/hardware/polkit-ssh-fix01.json`。源打包脚本 `configure-f8-release-root.py` 已补同等权限与持久化设置，尚未重建完整包。

SSH 只 enable 到 multi-user.target 无法随自定义 f8-desktop.target 启动。当前用户已主动开启 SSH，已将 ssh.service 加到 f8-desktop.target.wants；打包源加入 ssh.service 安装目标 drop-in，默认仍关闭、用户 enable 后适用于本机目标。冷启动持久化尚待复核。

## 麦克风：等待 A/B 实录

当前模拟增益 8（+24dB）、ALC Stereo、Max PGA7，可能在安静时抬升底噪；不能仅凭降低音量判定改善信噪比。

临时本地工具 `armbian/audio/mic-check.py` 已装 `/usr/local/lib/f8-pro/mic-check.py`，通过 user service `f8-mic-check-r1` 打开。每次14秒（准备2秒、安静4秒、说话4秒、安静4秒）；固定增益候选为 ALC Off、模拟增益5（+15dB），录后和退出均恢复原 mixer。录音仅存平板本人目录 `.cache/f8-mic-check-20261102/`，不上传；只读 results.json 的两声道静音/语音 RMS、截幅比例。当前尚无完整当前对比统计，未修改持久 UCM。

用户报告“录音程序退出1”。实查有13.91–13.95秒完整WAV，单采样启动探针也成功写入1帧却返回1；此前“程序没有录音成功”判断已向用户纠正。修复为只有主动定时SIGINT后、WAV格式与13–16秒长度校验通过时才容许返回1，真正错误写入本地record-error.txt并显示。SIGTERM关闭增加恢复mixer处理。修复后等待用户再做两次录音；应按实际results.json和主观反馈验收，不能写成底噪已修复。最新打开记录 mic-check-install04.json。

后续两段已有效完成：baseline13.9307秒、fixed13.952秒（mic-results06.json）。用户说第二项“只录制了一点”，核实不是时长截断，而是固定增益人声仅约-52.7dBFS，听感极轻；原设置左声道人声-13.2dBFS、静音-22.4dBFS，右声道人声与静音均约-22dBFS，没有明确语音响应。固定设置左声道语音/静音差约11.6dB，原约9.2dB，这只是一次环境/话音对比，不是已证实的降噪收益。mic-spectrum01.json确认主要不是直流偏移，右声道主要为噪声；并未因此证明硬件右麦损坏。

新工具保留两段结果，增加等语音RMS的左声道回放（仅生成本地临时回放副本，跳过启动2秒、峰值限制、25%流音量，不修改原录音或系统增益），避免仅用响度判断质量。增加第三项：ALC Left、Max PGA5、Left Capture8、Right Capture0、ADC Data Select Left Left，依然录后恢复，尚未持久化。需用户完成第三项并比较；现有两项无需重录。分析截幅统计改为忽略准备段。最新部署 mic-check-install05.json，等响度回放不是系统降噪修复。

### 左声道方案已试听验收、已持久化

用户确认“左声道测试更好”。第三项13.952秒，左声道人声-20.30dBFS、静音-32.43/-35.90dBFS，语音/静音差12.13dB，两声道准备段后的削波均0（mic-results07.json）。与原9.19dB相比约改善2.94dB；话音/环境未严格控制，不把此数当实验室SNR或驱动降噪指标。右通道已有同步人声但低约23.5dB，不能宣称输出两声道等幅或已恢复双麦阵列。

执行 `tools/prepare-f8-mic-left-default.py` 生成的root安装器：先正常停止临时测试APP，备份原UCM、asound.state和控制值于 `/var/lib/f8-pro/mic-left-20261102/`，保持Speaker/Playback整个前半段逐字节一致，仅将Mic设为用户验收五项：ALC Left、MaxPGA5、Left8、Right0、ADC Left Left；alsactl store。重启WirePlumber后单帧捕获验证所有控制值仍正确，正常WAV一帧、当前pw-record返回1的已知行为再次复现。证据 mic-left-default01.json，UCM SHA256 `60a812e71eb417369cf4854552cd77898259c5d8b94149bd88b1da52b54baf08`。未上传录音，未动扬声器参数/BOOT。普通应用复测和冷启动待验。

源 `armbian/audio/ucm2/HiFi.conf` 已更新，`configure-f8-release-root.py` 显式复制它，防止重新打包时沿用旧快照的Stereo/MaxPGA7。历史 `save-f8-mic-default.sh` / `add-f8-ucm-mic.sh` 仍记录旧配置，不要再执行覆盖新值。

用户随后用普通相机或录音软件复测，确认“正常，杂音比之前少”。麦克风当前方案已通过普通应用验收，冷启动后的保留仍待下一次GPU P1启动一并核对。下一步是用户进入Loader仅刷GPU P1 BOOT，再经SSH检查三档频率、温控映射和实际负载稳定性；当前还不能记为GPU P1启动成功。

## 性能：定位到限频，尚未宣称修好

实际渲染器为 Mali-G610 MC4 (Panfrost)，Mesa26.0.3，硬件渲染正常。Panthor devfreq 只列 200MHz。三路 SCMI CPU 时钟均816MHz，cpufreq policy 为空；保留启动参数 cpufreq.off=1 和 rockchip_cpufreq_driver_init blacklist。空闲约44–45°C，未发现可据此认定的热降频。

旧 PM1/PM1A 解除 CPU 保护后均无法启动。6.1.172参考源码不等于当前6.1.115二进制；直接加载 vendor cpufreq-dt 也可能依赖被跳过的 Rockchip 初始化。必须独立核对后再做 CPU 候选，不直接取消保护。

GPU 原私有 OPP 表中300/400MHz已存在、状态 disabled，电压目标与200MHz同为675mV。GPU P1 离线候选只启用这两档，最高400MHz；增加80°C被动降频点和5°C回差，绑定现有 Panthor cooling device。实际6.1.115配置含 CONFIG_DEVFREQ_THERMAL=y、导出 devfreq_cooling_em_register；实机已确认 cooling_device0 为 devfreq-fb000000.gpu-panthor，当前max_state0，对应唯一200MHz。原GPU温控只有115°C critical，无降频映射。P1启动后还需核对max_state2、温控绑定和负载频率。证据 gpu-p1-before.json。

候选保持 R1a 的官方 Image、ramdisk、CPU参数、USB和相机节点，FIT与resource内DT同步更新。构建工具 `tools/build-f8-gpu-p1-boot.py`，候选目录 `outputs/armbian/f8-gpu-p1/`；以 preflight.json 为离线完成依据。未刷写、未测性能。回退使用保留的 R1a BOOT，只刷 boot 0x8000，不重刷 rootfs。

### GPU P1 已启动、短负载通过

本次SSH实查boot_id `689ed988-016d-4207-be6a-027b76495b84`，chosen marker p1-400mhz，三档200/300/400MHz可见，最高400MHz，原simple_ondemand不变。GPU thermal_zone5新80°C/5°C passive trip及cdev0绑定存在，cooling_device0 max_state2。电压675mV。CPU仍三集群816MHz。证据gpu-p1-start01.json。

工具 `tools/test-f8-gpu-p1.py` 先2秒预热，再同一glmark2-es2-wayland terrain场景1280×720 offscreen/finish，各6秒：限200MHz为22FPS，放开400MHz为50FPS；各14次采样分别全为200/400MHz。最高51.769°C，测试后max_freq恢复400MHz，未改变governor/min_freq。此次是单场景短测，长时间负载及温控实际触发未验证。原结果gpu-p1-benchmark01.json的fault_lines正则误把debug:/ramoops:当BUG/Oops，所列均为无关启动信息；工具已改为单词边界，不能把该数组非空误报成GPU崩溃。

同次冷启动后的麦克风五项配置正确、Polkit helper4755、SSH自定义target配置保留且直接可连（gpu-p1-bench-inspect01.json）。管理员窗口本次未重复人为触发，麦克风声学效果沿用用户前次普通应用验收。

### CPU P2A 已编译、待刷BOOT后手动加载

避免重新启用曾导致启动失败的vendor初始化。独立源码 `armbian/power/f8-cpufreq-p2.c`：仅816/1008/1200MHz，直接使用已存在SCMI时钟，不直接改PMIC；要求初始816MHz、已知8核拓扑、SCMI protocol0x14父节点arm,scmi-smc，读到小核>=750mV/大核>=800mV。升频前检查soc温度15–70°C，cpufreq cooling设备使用既有soc75/85°C映射；退出尝试恢复816MHz。标准cpufreq接口、默认powersave。此为保守定电压带上限实验，不是完整OPP/PVTM/DSU调频适配，未验证运行，不设自动加载。

先编译P2发现离线拓扑检查误要求SCMI子节点compatible，实际在父节点。已改为核对protocol reg和父compatible，另版P2A输出，不复用旧模块。P2A模块SHA f68a2ee6…11706f27，所有导入CRC比对实际官方6.1.115 Image（不是仅比对头文件）通过。模块已存平板 `/usr/local/lib/f8-pro/experimental/f8-cpufreq-p2.ko`，未加载/无autoload（cpu-p2-module-stage01.json）。

P2A BOOT以已验证P1为输入，只改chosen bootargs/CPU marker；Image/ramdisk逐字节相同，GPU和供电DT未动。移除cpufreq.off=1，设cpufreq.default_governor=powersave；保留原vendor/camera黑名单，新增cpufreq_dt_platdev_init黑名单阻止通用平台驱动抢先probe。SHA `a3a23fd7ea637cff25e333f7c52d212a9a9310f8b3ebb0b54a25a700301aa76e`，49,460,132字节，FIT/resource/内存容量及Windows完整读回通过。文件及刷入/回退步骤见outputs/armbian/f8-cpu-p2a/README.md。只刷boot0x8000；P2A未启动验证。下次必须先核对marker/core.off/无意外policy，再手动加载并逐集群短测，不能直接启用开机模块或拉满频率。
