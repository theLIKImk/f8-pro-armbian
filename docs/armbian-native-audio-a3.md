# A3：音频MCLK外部输出门控候选（2026-11-01）

**2026-11-01 持久化验收（覆盖下方“默认路由/音量策略和跨重启持久化尚待处理”）：已通过。**路由与开关：`asound.state` 固化 Speaker/OUT2 on、OUT1/Headphone off、spk on/hp off、左右混音矩阵 on、OUT2=0dB(30/33)、PCM=166(-13dB) 基线，`alsa-restore` 开机自动恢复。修复：删除残留 `/etc/alsa/state-daemon.conf`（曾令 alsa-restore 条件不满足被跳过）。桌面音量：WirePlumber 用户态持久化（default-nodes/default-routes）并开机写回，经两次 SSH 协调重启实测自动恢复，用户确认重启后音频正常。工具：tools/apply-f8-audio-default.sh（含备份）、tools/finalize-f8-audio-state2.sh、tools/fix-f8-alsa-restore.sh。设备层(route)音量细调默认值未再深入（用户停止该项，桌面调节正常即可）。

最新验收：用户明确确认softtone-02听到了“两段音调”，扬声器短音播放通过，preflight audio_playback_verified=true。A3作为后续适配BOOT基线。试验采用临时Speaker/OUT2路由，结束已恢复。电池继续暂缓。

实测更新：用户已刷入A3并启动，boot_id b6220a3a-0022-436d-bb1d-0210a2782bdf，SSH地址不变。运行DT证实codec clocks指向provider phandle462；静音S16_LE/48000双声道PCM运行时i2s0_mclkout_to_io enable/prepare均1、频率约12287999Hz，aplay和混音器恢复退出0。门控软件状态通过，未测量物理引脚波形。KDE Wayland、Panthor、键盘、正确背光pin、原生rw及持久化通过。随后只做一次两秒低音量左右声道试验，pw-play退出0、混音器恢复0，等待用户声音反馈；audio_playback_verified仍false。新证据local/hardware/armbian-native-audio-a3-20261101-01/。下方尚未刷入说明为历史构建记录。

A2已冷启动验证：实际亮度可调，不再马达振动。SSH 192.0.2.227/f8test，boot_id 0c6411d0-54bf-4a57-98d6-0e1cac9a7fd7；GPIO4_B2由PWM14m1占用，GPIO3_C2空闲。原生p6根可写、持久化标记、KDE Wayland和屏幕键盘正常。当前仍A2；尚未进入本轮Loader或刷A3。

A2低音量两秒测试进程退出0且混音器已恢复，但用户明确只听到短促咔哒声，不能算扬声器通过。随后关Speaker/Headphone做全零PCM检查，hw:0,0以S16_LE/48000/双声道运行，aplay退出0，混音器恢复。内部MCLK约12.288MHz并启用，但i2s0_mclkout_to_io门控enable/prepare计数均0。证据在local/hardware/armbian-native-audio-a2-20261030-01/，尤其silent-clock-01.json。该现象支持继续测试外部时钟路径，并不证明已找到唯一无声原因。

A3基于已验证A2，仅给现有/clocks/mclkout-i2s0@fd58c318节点增加未使用phandle，并将/i2c@fec90000/es8388@11的clocks指向该节点。该节点为rockchip,clk-out、#clock-cells=0，其父时钟与codec原先直接使用的CRU时钟相同。codec assigned-clocks及12.288MHz设定保持不变。A2背光修复保留；kernel/ramdisk/resource逐字节不变，电池配置不变。

文件：outputs/armbian/official-f8-native-audio-a3/BOOT_ONLY_ARMBIAN_NATIVE_AUDIO_A3.img

- 长度49426624字节，适合64MiB BOOT分区。
- SHA256：831ca9b5eb6595e2e3b91353c26964aeb759381c822d83ef09200096c6126df3。
- DT逐属性限定差异、FIT哈希与FDT增长内存边界检查通过。
- 冷启动、物理MCLK波形和实际扬声器出声均尚未验证。构建已完成，不要重复运行。

用户手动进入Loader后，RKDevTool只选择boot一项，地址0x00008000，选择上述A3文件并执行；不勾rootfs、Loader、recovery，不擦除Flash。重启联网后先通过已固定公钥SSH核对新boot_id、实际DT时钟引用、声卡/桌面和背光，再用关闭输出的静音PCM检查IO门控计数。确认后才进行一次新的编号低音量短音并让用户判断，不提高音量或盲目切换GPIO，不录制麦克风。若异常，BOOT-only回退已验证A2（SHA bd7277d09b7928ef554960986ab14076292a57a247aac59d13bd57bd2f7376ec）。

不重刷rootfs，不重建完整桌面包或私人备份。继续暂缓电池/充电/PD，现有服务配置保持。
