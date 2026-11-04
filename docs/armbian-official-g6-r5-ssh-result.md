# G6 r5 SSH实测通过，待换充电器（2026-10-30）

更新：用户已确认换接充电器。实际Wi-Fi SSH连续读取4份快照，保存同目录ssh-after-charger-01.json；同一boot_id，无重启、0失败单元。采样窗口约30秒，CW4141/4132/4144/4166mV，对照接入前基线4121mV有所升高；SOC仍100%。BQ设定未改，0x11由基线152变154，但ADC转换未开启，不能将ADC数值当作时效已验证的输入电压/充电电流。只确认短时换接保持运行及实时采样，尚未验收有效充电电流、快充/长期温度和电池校准。

该BOOT可保留为当前远程诊断基础，不需要因为电脑数据线拔出而回退；这不表示充电管理适配已完成。后续要做供电限制/准确电量/驱动与保护策略，仍参考已知原厂参数及实测，不把2.944A设定直接当作实际电流。

用户报告启动成功、IP192.0.2.227。已使用原专用密钥和已知主机身份真实登录f8test，sudo读取确认Armbian/6.1.115-vendor-rk35xx；原SSH密钥/主机身份未重新生成。此刻确实在线，不再停在旧r3/r4失败状态。

换接前基线已保存local/hardware/armbian-official-g6-r5-20261030-01/ssh-before-charger.json，包含boot_id、内核、OS、RAM挂载、各服务、GPU及完整BQ/CW原始寄存器。配置prepare/network active/exited/success，SSH/power/status active/running/success；图形初始化成功退出，旧wayland服务inactive/success，自动弹窗不运行。GPU硬件像素读回通过。用户尚未明确单独验收状态页外观，不仅凭服务running认定画面正确。

基线电量计单读4121mV、SOC100%、normal，曲线原厂匹配，样本年龄6.47秒；SOC100%与电压趋势尚未验证校准。BQ配置仍3A输入限流/2.944A充电设定/4.4V/64mA，CHG使能/OTG关/WD关；ADC为已有样本4.104V，未触发转换。设置值不代表实际电流，不凭CHG位宣称正在有效充电。

下一步已可让用户在保持平板开机和Wi-Fi连接的情况下，从电脑USB换接此前铭牌5V3A/9V2.22A/12V1.67A充电器，然后用户回复接好。通过SSH比较同一boot_id、采样时效、BQ状态/输入电压原始码、CW电压趋势。不要声称G6强制只允许5V；当前没有实现PD/HVDCP限制或新充电驱动控制。尚未执行实际换接，也未完成充电验收。

tools/ssh-f8-live.py + tools/read-f8-live-baseline.sh可读取完整状态，原始基线不得覆盖；后续采样应写新文件。capture-f8-live-baseline.py保护已有基线，不能重复直接运行。WSL启动时偶尔报root用户systemd session失败，但SSH命令实际返回0；别把WSL警告误判为平板故障。

当前BOOT可作为已通过Wi-Fi/SSH/驱动初始化的临时远程诊断基础；供电插拔/实际充电/长期稳定性尚未通过，因此未认定为完整供电基线。无后台监控或未完成构建。
