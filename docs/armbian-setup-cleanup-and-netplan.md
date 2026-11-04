# 新账户验收、临时账户清理与Netplan遗漏（2026-11-02）

用户确认R1a后账户创建成功并已登录新账户likimk，提出“F8 First Run”仍在。原因是R1/R1a只锁定、到期并设置nologin，没有删除当时仍运行向导的f8setup。现已在新账户的真实Wayland会话中完成延后清理。

## 实机结果

- 当前SSH用户likimk，UID1602，192.0.2.227；boot_id `7a5b6bd2-9762-4e2b-a225-9af9ecafb574`。用户本机启用了正常ssh.service，新系统没有继承旧测试授权key。后续不要调用旧f8test固定账户脚本。
- 新安装SSH主机采用独立首次连接记录 `/var/tmp/f8-pro-armbian/post-wizard-likimk/known_hosts`，未覆盖旧主机记录；ED25519指纹 `SHA256:XS9mqNQLlia6AOakeRu4osWr1oDrnd5oCejmQ3jbeGU`。该信任来自用户指定的重装后局域网地址首次连接，**不是用户提供指纹的带外核验**。随后连接均StrictHostKeyChecking=yes。临时认证凭据只经进程内存/stdin传递，未写入新增脚本、交接文档、日志或镜像。
- 首次设置complete.json记录likimk、zh_CN.UTF-8、Asia/Hong_Kong、密码登录。检查真实活动Wayland会话、旧账户固定UID1601/原home/nologin/锁定到期、旧UID无进程后，删除f8setup账户记录，不强制结束进程。
- **getpwnam已无f8setup，AccountsService ListCachedUsers仅User1602。** likimk账户正常。旧home已移至平板 `/var/lib/f8-pro/retired-setup-r1/home`，上级0700；旧setup专用sudoers规则已删除，账户设置缓存移入备份。没有递归删除目录，没有改当前Wi-Fi。
- 根文件系统实际已覆盖p6：底层246,960,619,520字节（约247GB/230GiB），df文件系统总计242,956,578,816字节，当前可用约226GB（元数据/保留块和GiB/GB计量不同，不能把这些都等同于厂商标称256GB）。扩容完成记录ok=true，最近检查grew=false表示已经到目标大小，**不是扩容失败**。未改分区表。
- 最终0 failed，马达空闲0；本轮未重启，未额外播放或更改相机、GPU、充电CPU等硬件配置。

证据 `local/hardware/post-wizard-read01.json`、`setup-cleanup-install01.json`、`setup-cleanup-final01.json`。这些文件不含密码、SSID或Wi-Fi密钥。

## 清理实现与后续打包

`armbian/first-run/setup-cleanup.py` 已安装 `/usr/local/lib/f8-pro/setup-cleanup.py`。默认仅检查，`--apply` 才执行；确认新用户活动Wayland登录后才清理，只针对f8setup/UID1601，未完成向导/未登录新桌面/旧UID有进程时等待。仅 `userdel f8setup`，不带-r/-f；先在同一文件系统原子移动目录到root私有备份，userdel失败时恢复目录。重复执行不会删除新用户。

同时准备 `f8-setup-cleanup.service/.timer`：开机90秒后检查、每60秒重试，未满足条件不操作，完成后自行停用。实机此次已直接清理完成，timer停用，未留周期任务。五组测试覆盖活动会话、异常身份拒绝、已完成幂等、实际目录保留及userdel失败恢复；实际运行又验证账户/AccountsService/目录权限。

`configure-f8-release-root.py` 已加入清理脚本、unit、timer及已有root-grow服务的后续集成；旧R1 ZIP没有重写，**这些源码变更不等于旧包已经更新**。未来重包另建版本，不覆盖原归档。

## 已确认的Wi-Fi清理遗漏

用户指出Wi-Fi连接仍保留，核查发现Ubuntu NetworkManager还有Netplan持久化配置：`/etc/netplan/90-NM-*.yaml`。R1只排除了NetworkManager连接目录，遗漏了此路径。已从**实际R1 ext4镜像**提取到内存并验证文件哈希及密码字段存在；只记录布尔值/摘要，没有导出SSID或密码。此前README/集成报告“无Wi-Fi密码”的声明不正确。

修正：后续快照排除整个 `/etc/netplan`，配置阶段只重建固定的通用NetworkManager renderer YAML，打包阶段要求目录中仅有该文件且内容精确匹配，同时仍验证NM连接目录为空。原R1 ZIP/镜像保持原字节，已在bundle.json标记 `private_do_not_distribute=true`、`contains_source_netplan_wifi_profile=true`、`requires_sanitized_rebuild=true`，旁边有KNOWN-ISSUES.md。**不要分发现有R1为通用干净镜像；需要另建版本重包。**

证据 `local/hardware/r1-netplan-private-profile-audit.json`（构建副本）、`r1-netplan-image-audit.json`（真实镜像）。当前平板Wi-Fi连接按维护需要保留，未以清理镜像源为由删除用户正在使用的联网配置。
