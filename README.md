# F8-PRO Armbian

F8 RK3588S 平板的 Armbian 移植记录、设备适配源码、桌面工具和测试镜像。桌面为 **KDE Plasma Wayland**，现用内核为 `6.1.115-vendor-rk35xx`。

## 下载与刷入

最新测试版：[2026-11-03 R2](https://github.com/theLIKImk/f8-pro-armbian/releases/tag/v2026.11.03-r2)。完整 BOOT＋ROOTFS ZIP 约 4.70 GiB，分为三个连续分卷。

1. 从 Release 下载全部 `.zip.001`、`.zip.002`、`.zip.003`，以及 `split-manifest.json`、`merge-release.py`，放在同一目录。
2. 使用 Python 3 运行 `python merge-release.py`。脚本逐卷校验 SHA-256，并校验合并后的完整 ZIP；不要单独解压分卷。
3. 解压完整 ZIP，按其中 `SHA256SUMS` 校验 BOOT 和 ROOTFS。ROOTFS 解压后为 16 GiB，需预留空间。
4. **先备份个人文件。** 仅适用于本项目已经验证的 F8 GPT 分区布局：RKDevTool Loader 模式下 BOOT 写 `0x00008000`，ROOTFS 写 `0x00078000`。不刷 Loader、uboot 或分区表。ROOTFS 会覆盖现有系统、账户和数据。
5. 首次启动通过图形向导创建账户、连接 Wi-Fi；预期由现有扩容服务扩展文件系统。没有预设登录密码。磁场校准及当前启动的陀螺仪静置校零需自行完成。

完整 ZIP SHA-256：`b6a2acc525a31a12df98a00c1d9364f60d29a9a1de02080bb8bfe9bef20212a8`。

**本份完整包尚未实际新刷或冷启动验收。** 已通过只读文件系统检查、87 项关键文件的 ext4 回读、隐私检查、ZIP CRC 和首次向导六页离屏预览。这些检查不能代替新刷启动验证。

详见 [发布记录](docs/armbian-release-20261103-r2.md)、[刷入说明](release/20261103-r2/README-刷入说明.txt) 和 [校验摘要](release/20261103-r2/checks-summary.json)。

## 已适配与已知限制

已在原运行系统逐项验证：KDE Wayland、开源 GPU、触摸与亮度、Wi-Fi、蓝牙扫描、USB Host/U 盘、扬声器与麦克风、前后摄像头基础预览/拍照/录像及兼容中继、运动/磁场/光线/接近传感器、自动旋转/自动亮度、霍尔合盖熄屏、振动和屏幕键盘反馈、CPU/GPU 手动调频、KDE 磁盘/GPU 监控、Fcitx5 中英文实体/屏幕键盘、时间同步与农历。

- 电池与充电采样仍待完善，不能依赖当前电量显示判断充电状态。
- 多指靠近、快速敲击及高采样率的触摸稳定性仍有限；默认保留原版触摸配置。
- 相机的分辨率、色彩管理、对焦、RAW 等高级控制待完善。
- 浏览器传感器使用兼容启动器；CoderTools 姿态绘制修正仅针对指定页面。中继不是通用 Android 传感器 HAL。
- 低音量曲线试验已撤回，使用原音频方案。

## 隐私与输入法

镜像中已清除 Wi-Fi 连接及密码、SSH 主机/用户密钥与 known_hosts、旧账户、个人目录和个人传感器校准。仅保留首次设置入口账户。SSH 默认关闭，用户启用时生成新主机密钥。

Fcitx5 云拼音使用 Ubuntu 软件包 `fcitx5-module-cloudpinyin 5.1.12-1`，默认百度后端、最小拼音长度 4。**云候选会向服务发送拼音查询**，可以在 Fcitx5 拼音设置中关闭；未打包个人词库或输入历史。

## 源码与构建

- `armbian/`：板级 DTS、驱动/中继/面板源码、首次向导和默认覆盖层。
- `tools/`：构建、安装、打包、分析与历史诊断脚本。
- `docs/`：适配过程与技术记录；较早的文档描述历史状态，以本页和最新发布记录为准。文档中的 `192.0.2.227` 是示例地址。
- `release/20261103-r2/`：本次公开发布的清单、隐私审计和校验摘要；大镜像通过 Releases 提供。

先读 [BOOT 构建说明](docs/BOOT-BUILD-GUIDE.md) 和 [R2 发布流程](docs/armbian-release-20261103-r2.md)。目前 BOOT 路线复用已固定的 Armbian 内核 Image，再适配 DTB、initramfs 和模块；尚没有完整锁定且独立验证的全内核源码重建路线。

本仓库是移植工作区的公开源码快照，**不是从空目录一键重现全部镜像的构建系统**。历史脚本含本机构建路径，部分输入来自未上传的官方镜像、内核源码/头文件、构建 sysroot 或组件产物。`local/`、原始硬件日志、凭据、下载缓存与历史整机镜像不上传。运行构建前应逐项准备输入并审阅脚本；不要批量执行历史硬件诊断脚本。

第三方组件来源及许可见 [THIRD_PARTY.md](THIRD_PARTY.md)。本项目与 Armbian 上游无官方关联。
