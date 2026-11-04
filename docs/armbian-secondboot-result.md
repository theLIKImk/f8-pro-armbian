# R2 真机结果：CPU 供电总线修正生效

2026-10-29，用户启动 R2 后报告 F: 日志盘。主助手确认卷标 F861R2，保存 15 个文件到 local/hardware/armbian-6.1-r2-20261029-01/；test-result.json 保存逐文件 SHA256 与结论。新内核版本和 R2 model、快照完成标记均已确认，未误用首测日志。

## 达到本轮目标

- PINMUX.TXT 确认 GPIO0_D1/D2（pin 25/26）由 fd880000.i2c 的 i2c0m2-xfer 占用，GPIO0-11 继续属于 SPI2；原 I2C0/SPI2 冲突不再出现。
- 0-0042 与 0-0043 均链接到 rk860-regulator，名称分别 rk8602/rk8603。dmesg 和 regulator_summary 均报告 vdd_cpu_big0_s0/vdd_cpu_big1_s0 已启用、800mV，约束 550–1050mV。这是驱动/寄存器读回信息，没有外部电压测量。
- 日志同时包含 initcall 黑名单解析及实际跳过 rockchip_cpufreq_driver_init 的记录；CPUONLINE=0，cpufreq policy 目录不存在，符合本轮单核/不运行 vendor OPP 校准的隔离设计。不能据此宣称 OPP、DVFS 或大核运行通过。
- 原 No available vop 和零大小 logo/LUT reserve 告警在此快照中消失。USB2 RAM 日志盘、eMMC 诊断链继续工作；未执行原根分区挂载或桌面。

## 未解决的事项

供电芯片绑定成功时仍有 regulator device-link -ENOENT，后续需从 regulator core 的 consumer/link 创建语义核查，不能把日志消失或电压调节可靠性当作已完成。RGA 聚合绑定仍报错，即使三个 DT 核心关闭；需检查聚合驱动的注册逻辑。初始 console 不可用，以及可选供电/SCMI/无线监管数据库等诊断仍在。

采集到的 dmesg 没有 panic/Oops，采集末尾约启动后 8.2 秒；没有长时间稳定性/负载测试。充电、显示/GPU、触摸、音频、网络和完整用户态仍未验收。

## 下一步

日志已全部保全，可立即按已有步骤只刷 boot 恢复 CURRENT-BOOT-ROLLBACK-64MiB.img 正常使用；尚未收到本次回退完成确认。当前不依赖平板在线继续本地分析。

下一轮先处理影响诊断可信度的供电 link/console 问题，再选择受控 OPP/多核验证或用户态启动；不要在未验证的充电策略下安排长期运行。R2、首测和回退镜像保持原哈希，后续测试包使用新版本。
