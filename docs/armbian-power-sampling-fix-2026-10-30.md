# ADC后台刷新缺口修复（第四十六轮）

第四十七轮更新：r6已由用户刷入，SSH确认新boot_id与运行文件匹配r6镜像，采样持久化三周期通过，不再只是r5 RAM热修。当前最新状态及验收证据见armbian-official-g6-r6-result.md；以下“r6未刷/r5重启丢修复”描述为第四十六轮历史。

用户指出充电采样可能有问题。本轮核查并修复的是测试BOOT的采集流程，**BQ/CW标准内核驱动仍未启用**，不能说已修好完整充电控制驱动。

## 排查结果

1. 官方6.1参考驱动读取REG12、50mA步进；Linux current_now充电取负号。原厂5.10真实Image离线反汇编同样读取属性0x11路径、乘-50000（0xef815c–0xef8184），不是不同电流比例。归档analysis/armbian/live-g6/vendor-charger/。这是静态实现对照，不等于原BOOT当前电流已实测；原BOOT参考脚本已准备但未执行。
2. 临时开启连续ADC约6秒，5组逐字节/批量读取完全一致，电压更新、电流原始REG12均0。原ADC模式0x1c→0x5c→0x1c恢复，充电参数不变；证据adc_audit-01.json。没有发现简单寄存器偏移/批读/倍数错误，但不能仅凭0码宣称实际电流0。
3. REG14=0x1f，PN3/revision3，与TI手册列revision1不同。仅PN或DT compatible不足以证明制造商/确切版本。未据此认定是其他厂兼容芯片，也未套用别的芯片换算。
4. 用户确认未拔线时，report-fix快照曾PG=false；随后state-04/adc-04恢复PG=true，新ADC REG12=4，按兼容映射约200mA，VBAT4.204V与CW4.204V接近、VBUS约4.7V。输入存在标志变化仍待进一步查USB-C/电源稳定性，不能归结成采样假象或线材故障。

## 确认的采集缺口与修复

旧live-power.sh每10秒只运行power-readonly.py，读取时间是新的，但没有主动刷新芯片ADC。因此寄存器快照时效不等于ADC采样时效，除手动采样外，ADC数据可能长期陈旧。此前手动单次采样中确有观察到变化，不能把所有旧0码都说成缓存问题。

新增power-refresh.py：先被动读PG；外部供电存在时执行受限单次ADC，观察busy/自动清零、核对参数未改，再被动读回完整BQ/CW，确认ADC原始字节吻合、时间<5秒且输入仍在，才发布fresh=true及电流估计。无输入不触发ADC；失败、锁冲突、陈旧或插拔转变时把估计值标为null，不伪装成0mA。

单次及连续采样助手共用/run/f8/bq-adc.lock排他锁；不会互相改ADC模式。只写ADC启动/模式位，不改限压限流、快充、OTG或复位。current estimate按兼容寄存器映射解释，actual_battery_current_ma仍null、未做外部仪表校准。

## 已部署与验证

只在当前r5 RAM upper更新，无刷机/重启，原文件备份：

- /run/f8/power-readonly-before-report-fix.py
- /run/f8/power-refresh-before-01/

新增bq-adc-oneshot.py、power-refresh.py及更新live-power.sh，重启现有f8-live-power.service。3周期验证均fresh=true、ADC年龄0.194–0.208秒，电流原始码5/兼容估计250mA，BQ4.224V、CW4.196–4.211V，SOC99.11→99.27%；充电配置未改。证据sampling-refresh-fix-01.json。服务active，SSH同boot。此为采样刷新验证，不是完整充电/PD/长期安全验收。

所有数据在local/hardware/armbian-official-g6-r5-20261030-01/；另有sampling-report-fix-01.json、state-04.json、adc-04.json。修复采集流程未改变上述历史原始文件。

测试覆盖单次消息与拒绝路径、连续模式错误恢复，以及新样本接受/过期/无busy握手/配置改变/原始字节不一致/输入消失等拒绝条件。报告analysis/armbian/live-g6/*fixtures.json。

资料：TI手册https://www.ti.com/lit/gpn/bq25890 ，官方内核读取源码已归档。不用0mA、SOC100%或VDPM单一标志直接判定实际充电。

## 持久化候选r6

已将相同修复打包至：

outputs/armbian/official-f8-live-g6-r6/BOOT_ONLY_ARMBIAN_26.8.1_LIVE_G6_CANDIDATE.img

50080260字节；SHA256：839dff537aceda1f8aa7ca0b92f6f31ec2fa1e6d4c8b6026bda029d57e06106d。

内核/DT/固件/根镜像及充电限压限流不变，保留SSH/无弹窗/状态页。实际init安装循环、服务图、FIT/CPIO/FAT/shell/内存检查通过。r6完整冷启动尚未真机；已验证的是相同采集组件在r5 RAM运行。preflight明确区分ADC启动写入与充电策略写入，不能继续用“全程寄存器零写入”描述。

**当前仍是r5加RAM修复，充电器插着、Wi-Fi SSH在线**。现在无需重刷；如果直接重启旧r5会丢失RAM修复，下次要保留此功能应按既有流程只刷r6 boot（LBA0x00008000，分区0x00020000扇区），不重传rootfs。未确认用户刷r6，不得标已部署。

平板f8-live-power现有服务持续刷新采样；没有宿主机后台监控、子代理或自动刷机。下一步观察接电稳定性、准确性及USB-C/充电策略，原BOOT对照仅为准备选项，不要求用户此刻回退。
