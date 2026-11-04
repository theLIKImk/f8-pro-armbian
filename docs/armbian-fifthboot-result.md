# R5 真机结果（2026-10-29）

确认 F: 卷标 F861R5。23份日志保存在 local/hardware/armbian-6.1-r5-20261029-01/；summarize-f8-fifthboot.py 检查实际日志并生成逐文件大小/SHA256及结论 test-result.json。没有修改平板或旧测试镜像。

## 本轮通过

- Trixie systemd继续作为PID1，f8-evaluation.target active，CPU0–7在线，ttyS2 console保留。
- SYSSTATE为running，FAILED为0个失败单元。systemd-resolved以systemd-resolve用户正常active/running，Result=success；journal不再有200/CHDIR或该服务journal socket拒绝访问。
- /实际0755；STEPS显示3个注入单元全部0644，PERMS确认旧SSH hostkey单元0644；旧world-inaccessible/world-writable/executable告警在本次journal中消失。
- User=nobody临时服务成功读取/etc/os-release，exit_code=0。这证明非root遍历/读取路径已恢复，不是仅屏蔽resolved。
- 原Arch p6仍ext4 ro,norecovery，SquashFS哈希验证成功且只读，根overlay upper/work仍在/run tmpfs。hostname为f8-pro-eval。

启动完成的systemd计时为21.534秒；kernel消息快照到约38.16秒，无panic/Oops。该时间不是长时间压力或休眠稳定性验收。设备journal日期来自内置epoch，实际测试日期是2026-10-29。

## 仍待推进

显示/GPU在当前DT中禁用，/dev/dri与/dev/mali不存在；这符合诊断设置，不代表GPU驱动已失败或硬件不支持。下一步核对VOP/VP2→DSI0、IOMMU、面板电源/复位/背光及GPU驱动配置，再准备图形候选，目标仍为KDE Plasma Wayland。

regulatory.db文件确实缺失，早期cfg80211加载失败；后续无线准备需补固件/监管数据库。RGA聚合绑定错误、部分电源查找debug信息、libbpf不可用与unmerged-bin提示仍存在；本轮零失败单元不代表这些问题已解决。

DNS服务正常启动不等于联网DNS查询成功。本轮仍没有网络SSH、Wayland/SDDM、触摸、充电、DVFS或负载测试。日志已保全，可以只刷原BOOT回退使用/充电；尚未收到本轮回退确认。无后台任务。
