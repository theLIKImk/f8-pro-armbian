# 扬声器低音量曲线试验：已撤回

2026-11-03。用户需求：30%以下也能清楚听见。最终用户要求“没声音，算了恢复原状”，已完成恢复，后续不要自动重新启用本次实验。

## 当前有效状态

- 默认输出恢复 `alsa_output.platform-es8388-sound.HiFi__Speaker__sink`，只剩原始一个扬声器输出。
- 音量恢复调整前48%，未静音。PCM恢复154/192（−19dB），Output 2仍24/33（−9dB），Speaker/OUT2开关均开启。
- 新增 `f8-speaker-volume.service` 已停止、禁用并移出有效路径，用户systemd查询为not-found；全局启用链接及KDE自启动入口已移除。
- 新增虚拟输出和试验进程已停止；实验配置、插件、服务移到平板 `/var/lib/f8-pro/backups/speaker-volume-v1/disabled-r3/` 留存，不自动运行。
- 本地rootfs overlay中的本轮全部文件已撤回。没有重打BOOT/完整ROOTFS镜像，没有改麦克风、原UCM文件或原有filter-chain服务。
- 真实播放恢复后的听感未另要求用户测试，不将只读控制状态恢复等同于新的主观验收。

## 试验经过与限制

原生Pulse音量采用立方幅度曲线，30%约−31.37dB，输出端另固定−9dB。尝试用只针对扬声器的PipeWire filter-chain建立独立音量曲线，物理PCM临时固定100%，模拟输出上限未提高。

1. R1线性幅度曲线：用户反馈主要是低音量太响，并非明确破音。
2. R2温和底部提升曲线：用户反馈没声音，20%固定短音也未听到。
3. R3 `sqrt(native amplitude)`（UI幅度的1.5次方）：编译本地LADSPA小插件；用户仍反馈没声音，要求恢复，停止继续适配。

三版在隔离null sink上的0/10/20/30/100%生成音频测试均符合公式；**这只能证明数字滤波结果，不能证明实际扬声器端到端可用**。R3的音量/静音服务重启记忆及停止时恢复等效物理音量通过。后续不能凭这些测试称“音量问题已修复”。没有证明后两版无声的最终原因。

R1枚举Props中的Gain值保持0来自控制缓存，不能据此断定DSP实际没有增益；随后采用隔离生成信号测试替代。R2服务验证因检测到VLC而在改动前主动退出，并未完成该轮重启测试。R3服务验证通过后，用户依然报告实际无声。

## 证据及源文件

- 原始读取：`local/hardware/volume-curve-before01.json`。
- 数字信号验证：`volume-signal-test01/02/03.json`。
- R3服务验证：`speaker-volume-verify03.json`。
- 最终恢复：`local/hardware/speaker-volume-restored01.json`，restored=true；PCM/Output 2和48%与初始值吻合。
- 回退脚本：`tools/restore-f8-original-volume.py`。
- `armbian/audio/f8-speaker-volume.conf`、`speaker-volume-service.py`、`f8-soft-volume.c`、`f8-speaker-volume.service` 等仅保留实验源文件；不在overlay、不应加入发布包。
- `tools/install-f8-speaker-volume.py` 是实验安装器，不要在用户再次明确要求此方向前运行。

LADSPA头文件参考PipeWire 1.6.2官方源码：
https://github.com/PipeWire/pipewire/blob/1.6.2/spa/plugins/filter-graph/ladspa.h

原始低音量问题保持未解决；用户选择恢复原状。
