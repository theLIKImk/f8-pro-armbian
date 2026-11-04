# R1 首次开机向导与完整测试包（2026-11-02）

> **R1归档不是可公开分发的干净包：**实际镜像确认Netplan残留源Wi-Fi配置，原“无Wi-Fi密码”声明错误；已标记私用并修正后续打包源，须另版重建。R1a后的新账户登录/扩容及临时账户清理已经实机核验，见[最新记录](armbian-setup-cleanup-and-netplan.md)。

> 实机已启动R1，但账户提交失败，且12GiB文件系统未自动扩容。已生成[仅刷BOOT的R1a修复](armbian-first-run-r1a-repair.md)，待刷入验证。旧R1 ZIP校验通过不等于向导实机通过；新部署应配R1a BOOT。

用户已授权首次开机图形向导：语言/时区、用户密码、可跳过的Wi-Fi、功能与限制介绍，完成后登录自己的KDE账户；随后制作BOOT＋ROOTFS测试包。本轮不刷写平板。

## 向导与验收

源码 `armbian/first-run/first-run.py`、`first-run-apply.py`、`native-prepare.sh` 及两个desktop入口。使用已有PyQt6，触摸尺寸控件、按可用屏幕缩放，密码不放命令行/日志/完成记录。设置由普通的f8setup本地自动登录会话显示，sudo只允许无额外参数的固定账户创建helper，不授予通用免密码sudo。

步骤：欢迎 → 语言/时区 → 账户/设备名（默认密码登录，自动登录须勾选）→ Wi-Fi系统设置（可跳过）→ 使用指南 → 提交设置。提交时禁用取消/关闭，失败保留可重试入口；成功后锁定并到期设置账户、禁用其登录shell，点击按钮退出到SDDM。新用户属于sudo/video/render/audio/netdev，使用自己的密码管理系统。应用菜单可重新打开只读“F8 使用指南”。

1. 真实平板已运行 **预览模式**；用户明确“界面、触摸和键盘都正常”。预览不会创建账户或更改系统登录。六页真实ARM64离屏截图在 `local/hardware/first-run-preview-r1/`，已人工检查表单、文字、末页；日志 `first-run-preview01.json`、`first-run-render02.txt`、`first-run-gui-preview01.txt`。
2. `tools/test-f8-first-run.py` 四组测试通过：非法字段/路径拒绝、成功及无密码落盘、重复提交拒绝、密码阶段失败回滚后重试。测试只在临时目录操作，不能在Windows直接运行依赖fcntl的Linuxhelper，应在WSL运行。
3. `tools/verify-f8-first-run-native.py` 在独立rootfs内实际执行ARM64 helper，真实useradd/chpasswd/usermod/localedef/chown；密码登录和自动登录两种配置均通过，密码状态P、新家目录默认配置所有权、保护盖服务链接、旧设置账户禁用以及重复提交拒绝均检查。试验账户与身份数据库恢复，不进入打包产物。证据 `first-run-native-test.json`。
4. 首轮ARM64测试发现useradd没有完整复制skel，**不能把普通用户创建成功视为硬件默认配置成功**。现helper显式复制受控skel，再设置密码/所有权，重新完成两种模式的实际测试。失败记录保留在工具运行历史。

当前实机仍f8test正常会话，仅新增预览缓存和一次性预览unit；未替换其实机账户/启动服务。账户创建验收属于离线ARM64集成，**新镜像首次冷启动、SDDM实际新用户登录及重启恢复仍待验**。

## 打包基线与清理

独立工作目录 `/var/tmp/f8-pro-armbian/release-r1/rootfs`，从旧干净桌面root复制后通过固定SSH主机密钥的只读rsync同步已运行平板，保留ACL/xattr/所有者/硬链接与系统/硬件资产；不是块级原子快照。源 `/dev/mmcblk0p6` 全程未写入，私人home/root、Wi-Fi连接、SSH主机密钥、蓝牙配对、浏览器资料、日志、服务缓存等在传输时排除，用户只取明确允许的板级默认文件。

随后在副本中：

- 移除f8test/f8gpu及旧测试SSH授权公钥、旧免密码通用sudo；重建锁定的密码数据库与独立f8setup。
- 替换会重建测试账户的native/desktop prepare；C4所需 `/etc/f8-pro-native-desktop-t1` 标记保留。
- 机器ID清空，主机密钥首次开机独立生成；SSH默认不启动，解除旧测试mask以便以后用户主动启用正常ssh.service，禁止远程root登录。
- 清空密码历史与PPP认证文件；`/etc` 私钥PEM标记扫描为0，最终再次核对无主机私钥、授权文件、无线连接和私人home。
- 旧USB自动日志盘与桌面用户取证autostart关闭，保留硬件启动及现有USB OTG服务。未改充电/CPU策略。
- 新用户skel包含虚拟键盘/30ms按键振动、霍尔屏幕服务、应用入口；不带原用户指南针校准。扬声器/麦克风UCM与WirePlumber、相机IQ/中继/浏览器兼容、传感器、USB、蓝牙、H2马达模块均列关键文件摘要。

BOOT直接复用C4 SHA256 `fbbfa1ece55b3c62decbd10ae9c2ac98ed5d717dd5f8b941c49004deb6c0903a`，不重编内核或更改DT。官方Image SHAa67daf71…c37b7、FIT各段哈希、resource DT一致、现有init所需helper/标记及根UUID逐项核对。根UUID保留 `69056675-4a48-4006-a3f3-5132c00cc6f2`，12GiB ext4；rootfs0x78000、boot0x8000，不改GPT。

## 构建与产物状态

流水线：

1. `tools/stage-f8-release-root.py` → snapshot-complete.json（已完成）；含SSH主机信任校验，禁止重跑覆盖完成快照。
2. `tools/configure-f8-release-root.py` → configured.json。
3. `tools/verify-f8-first-run-native.py` → first-run-native-test.json。
4. `tools/finalize-f8-release-staging.py` → 更新关键资产摘要、检查完整sudoers及C4启动守卫。
5. `tools/build-f8-release-r1.py` → 12GiB ext4、e2fsck、从实际镜像debugfs读回全部关键资产、哈希、ZIP.part。未完成mkfs不可直接重跑覆盖。
6. Windows原生 `tools/verify-extract-f8-release-r1.py` 逐项解压/验证ZIP，生成NTFS稀疏原始刷机文件，完成后才改名ZIP并写bundle.json。**bundle.json才是完成依据**。

输出 `outputs/armbian/f8-armbian-r1/`。首次生成ext4过程中，发现密码历史/PPP认证残留，已停止构建并只丢弃明确路径下的未完成镜像；清空副本认证残留后重新构建，操作记录 `auth-scrub.json`、脚本 `scrub-f8-release-auth-history.py`。该一次性清理脚本只适用于当时未完成镜像，不作为日常构建步骤重复执行。

当前：**完整测试包与Windows原始刷机文件均已完成并验证，尚未刷入。**

- `F8_ARMBIAN_R1_TEST.zip`：2,617,784,221字节，SHA256 `d3b068bf2536e9d98329d12a0e91df0656a23b4a54dac548a315757530629c6b`。
- `flash-files/ROOTFS_F8_ARMBIAN_R1.ext4.img`：12,884,901,888字节，SHA256 `444c80ddf7220537e3a40595e08efb191599dab096393c101b0f6ba4e6d98dde`。
- `flash-files/BOOT_F8_ARMBIAN_R1.img`：49,453,800字节，SHA256仍为上述C4。两个Windows文件以NTFS稀疏方式存储，逻辑字节和普通原始镜像相同，不是压缩镜像。
- ext4五阶段fsck、全部关键资产从镜像读回、ZIP全部七项解压校验、Windows原始文件全量回读/格式/大小/分区容量检查均通过。完成依据 `bundle.json`、`flash-files/flash-files.json`、`flash-files/native-readback.json`。新root已登记至 `tools/check-flash-file.py`。
- 预览进程已由用户关闭，无额外自启动；真实Qt自动平台确认wayland，KDE登出方法只读确认存在，最终实机马达空闲0。当前平板仍原f8test账户/SSH，不是新包系统。

用户使用步骤见 [刷入与首次设置](flash-f8-armbian-r1.md)。**下一步才是用户进入Loader后刷两项并验收首次向导、创建账户、SDDM登录及重启恢复，再回归硬件。**新镜像不带旧SSH授权，SSH默认关闭，刷入后不能沿用旧f8test自动连接脚本。仅复制旧BOOT也不能回退新ROOTFS；私人备份未放入通用包。
