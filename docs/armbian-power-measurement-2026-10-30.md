# r5接充电器后稳定性、单次ADC与故障核验

最新第四十五轮：用户已接回原充电器/原线，state-03.json与adc-03.json已保存。同boot/SSH在线/0failed，PG恢复true、CHRG_STAT恢复2。新的单次ADC为VBUS-good=true/4.8V、BAT4.124V（拔下时3.964V），充电ADC仍0mA、VDPM=true、IDPM=false，采样启动自动约0.105秒清零、充电配置不变。CW本次状态采样为96.1015625%/4107mV，与ADC时刻不同，不能强行对齐成同一瞬间的校准误差。

这组“接入→拔下→接回”外部输入识别和电池接续供电测试通过，实际有效充电仍未通过/未确认。拔下时PG/VBUS失效、CHRG_STAT0/DPMfalse，接回后恢复；不要把电压恢复直接宣称为净充电电流正常。当前物理状态为**原充电器已接入、r5开机Wi-Fi在线**，无需再要求用户接回。SOC从先前100%降到96.1%，百分比不作为满电完成依据。

后续重点为USB-C输入识别/供电能力及BQ电压调节策略；当前寄存器VINDPM状态与0充电ADC提示输入侧限制，但不单凭此认定线坏或电池坏。无需为此次对照改BOOT或充电门限。现有r5可保留远程诊断；尚无新充电控制驱动/PD协商适配完成。

最新第四十四轮：用户已明确拔下充电器。state-02.json确认同boot、SSH未断、0失败单元；BQ power_good=false、CHRG_STAT=0，CW99.41796875%/3968mV。adc-02.json再次只触发单次ADC，约0.105秒自动清零、控制配置前后一致；VBUS-good=false（不把失效ADC码套公式成2.6V），电池3964mV、充电ADC0mA、VDPM/IDPM均false。BQ与CW此时相差约4mV，拔下前后状态确实变化，百分比也已低于100%，不是完全固定显示。

这证明本次外部输入移除识别及电池接续供电/远程采样正常，尚未证明充电器接入后的实际净充电。当前物理状态为**充电器已拔下、平板开机Wi-Fi连接**。下一步请用户接回同一只充电器/同一条线，确认后保存state-03和必要的adc-03对照；尚未收到接回确认。不要现在记录已接回或自动切换BOOT。

最新补充（第四十三轮）：用户没有备用C-C线，只有C-to-A，并指出显示100%。不再要求换不存在的线。100%下接近0充电电流可能是正常末期现象，因此不能单凭0mA判断充电失败或线材/电源异常。复查state-01.json：同boot、0failed、数据年龄1.82秒，CW100%/4156mV；BQ CHRG_STAT仍2（非3充电完成）。两个读数尚未形成“准确满电”的一致证明，也不能仅凭4.156V认定电量计错误；电池类型、曲线及充电策略仍需验证。

下一步优先在现有r5/同线/同充电器下做插拔识别对照，不刷BOOT、不改电量曲线、不人为深放电。请用户先拔充电器、保持开机Wi-Fi，确认后只读PG/VBUS与CW状态，必要时用独立编号再做单次ADC；再由用户接回原充电器对照。当前仍接充电器，尚无拔下确认。sample-id参数已支持01–99，所有新快照/runner分编号，不覆盖首测；锁存fault文件仍只能单次，不能盲目重读。

日期2026-10-30。当前仍是G6 r5、192.0.2.227，Wi-Fi SSH正常。用户确认充电器通过USB-C到USB-C直接连接，无转接头。

## 已保存证据

目录local/hardware/armbian-official-g6-r5-20261030-01：

- stability-01.json：6份间隔8秒的40秒只读稳定性快照，同一boot_id；SSH/power/status均active、0失败单元。CW4147–4164mV、SOC一直100%；SoC及片内温度45.307–46.230°C。该温度不是电池温度。
- adc-01.json：一次REG02 CONV_START采样启动，约0.105秒后自动清零；前后所读控制/充电配置逐项一致。电池ADC4.164V、VBUS ADC4.8V/VBUS-good=true、充电电流ADC0mA、VDPM=true、IDPM=false、thermal regulation=false、CHRG_STAT=2。
- fault-01.json：明确读取REG0C两次，第一次历史锁存值先保存到目标RAM /run/f8/bq-fault-latched-first-01.json，再读当前状态。两次均0，无watchdog/boost/电池过压/NTC/充电fault报告。读取锁存会清掉历史记录，此过程已明确记录，不能再称本次完全未影响故障锁存。

stability原始kernel_alerts中的4行ramoops初始化是正则Oops:的误匹配，不是实际Oops。后续脚本改用词边界，原始文件不覆盖。0失败单元及原日志中没有所筛选的实际panic/热关机事件；不扩大为完整长时稳定性验收。

## ADC操作边界

此前power-readonly.py没有触发ADC，BQ原始电压/电流可能是旧样本。本轮新脚本armbian/power/bq-adc-oneshot.py只在原厂I2C6 m3、节点disabled、无内核驱动绑定、PN=3、ADC/DPDM不busy时，写REG02原值|0x80。没有改限压、限流、PD/OTG、reset、曲线或连续采样开关；不强制清除超时位。不应把它泛称为纯只读测试：有1次ADC启动写事务，充电策略写入为0。

adc-01.json历史字段configuration_value_writes=0指充电配置未更改，adc_start_strobes=1明确记录采样写；后续源代码将前者改名charging_policy_writes以免歧义。未修改已保存原始证据。无需重刷BOOT，脚本通过SSH临时执行。

tools/test-f8-adc-oneshot.py离线验证实际I2C消息：写仅到REG02，唯一变化bit7；busy/continuous/DPDM及错误PN拒绝；超时不追加写；不读取REG0C锁存。真实测量随后验证自动清零/配置不变。测试报告analysis/armbian/live-g6/adc-oneshot-fixtures.json。

依据TI BQ25890资料9.2.8，单次CONV_START会自动清零，典型结果不超过1秒；9.2.6 DPM描述输入电压限制时可能将充电电流减到零；REG0C两次读取用于历史及当前故障。来源：https://www.ti.com/lit/gpn/bq25890 。芯片ADC为估算，不能替代校准的电流表/电压表。

## 当前结论与下一步

接充电器后系统能持续运行和远程采样，但**尚不能认定有效充电正常**。现有新样本为0mA且VDPM=true，更符合输入电压调节限制充电的现象；不能据此单独认定充电器损坏、线材不好或内核策略一定有错。SOC100%也尚未校准，不能拿它证明电池已满。

已向用户提出单变量对照：如有另一条C-C线，仅换线而保持原充电器和系统开机；如无备用线，可恢复原BOOT用相同线/充电器对比。等待用户答复/确认物理操作，尚未换线或回原BOOT。不要自行声称对照完成，也不要直接降低VDPM门限/提高电流或启用高压快充。

需要新的ADC/稳定性复测时，现有capture-f8-next-test.py保护*-01.json和runner不覆盖；应先为新采样提供独立编号文件，再运行，不盲目重跑覆盖首测。fault首读记录文件也有排他保护，后续如需再读应保存独立编号，不能复用旧锁存历史。

无后台监控，无新BOOT；r5仍是远程诊断基础，供电管理未验收完成。
