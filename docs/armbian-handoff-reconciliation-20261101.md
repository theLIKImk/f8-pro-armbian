# 其他 AI 改动接续核对（2026-11-01）

本记录覆盖旧的“等待音频重启验收”“电池组件尚未接入”等状态。已阅读 HANDOFF、TODO、音频 A3、麦克风、电池组件和电源三档状态文档，并通过固定主机公钥 SSH 只读核对实机。此次没有重启、刷机、加载驱动或修改平板配置。

## 实机核对结果

- IP `192.0.2.227`，用户 `f8test`；boot ID `a56f9a1a-ca82-4f4d-96d3-fbf4df432102`。
- 系统 `running`，失败单元 0；SDDM、USB OTG、电池绑定、ALSA restore、UPower 均 active。
- 默认音频输出是 `HiFi__Speaker__sink`；麦克风 `HiFi__Mic__source` 已枚举。本次未播放声音或录音，实际播放、录音和重启用户验收沿用其他 AI 的记录。
- CW2015 `present=1`、容量 94%、状态 `Discharging`。绑定服务退出 0，本次启动约 6.63 秒完成，补充验证了加固后的启动时序。此结果不代表充电状态或电流已适配。
- CPU 三个集群 SCMI 时钟读回 816MHz，无 cpufreq policy；cmdline 仍含 `cpufreq.off=1` 和 vendor initcall 黑名单，与回退后的保守基线一致。此次未独立重读 BOOT 分区哈希。
- polkit helper 为 root:root、4755；socket masked。认证功能验收沿用原记录，本次不读账户哈希，也不重复密码操作。

## 配置资产接续

实机 HiFi.conf 已增加 Mic，项目旧版本仍只有 Speaker。已将实机原文同步到项目 `armbian/audio/ucm2/HiFi.conf`，SHA256 `e0544d91b3ba9404655d2b5759c4f1b7f37cd21ccaa0f66cf9352872caf90d90`。

实机 WirePlumber 配置已保存到 `armbian/audio/50-f8-ucm.conf`，后续打包需安装到 `/usr/share/wireplumber/wireplumber.conf.d/50-f8-ucm.conf`。未改变全局规则范围或实机行为。完整文件内容、哈希、ALSA 状态和电池服务保存在 `local/hardware/handoff-reconciliation-20261101.json`。该快照不含私钥或密码。

USB 两个 root 服务资产哈希仍与 U5 runtime-integration.json 一致。该清单仅覆盖 USB，不能作为新音频、麦克风、电池及 polkit 的完整安装清单；下一次完整 root 打包前应补齐这些资产。不要重新运行旧 UCM 安装器，否则可能覆盖 Mic 配置；旧音频验证器固定了旧 HiFi 哈希，不能据此判定现版本失败。旧重启脚本硬编码过期 boot ID，本次未运行。

## 调频结论的证据边界

PM1 和 PM1-A 均不启动，恢复 U5 后可启动；这支持继续调查解除 vendor cpufreq initcall 黑名单后的路径。没有本次内核日志，尚不能断言已定位到具体崩溃位置。不要将运行态 probe、模块加载或 SCMI 调频称为“零风险”；先查匹配内核源码、错误路径和可观测启动方式，再设计下一次测试。BQ25890 充电策略与 PD 参数继续不改。
