"""Create a public source snapshot in the separately cloned repository."""
from pathlib import Path
import json,re,shutil,hashlib,ast,subprocess,sys
P=Path(__file__).resolve().parents[1];W=P/'local/github-publish-20261104';R=W/'repository'
assert (R/'.git').is_dir()
excluded={'final-f8-pw-check.sh','verify-f8-password.sh','set-f8-password.sh','set-f8-password2.sh','set-f8-password3.sh','set-f8-password-direct.sh'}
copied=[]
def copy(f):
 rel=f.relative_to(P)
 if '__pycache__' in rel.parts or f.suffix in {'.pyc','.pyo'}:return
 assert not f.is_symlink(),str(rel)
 dest=R/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(f,dest);copied.append(rel.as_posix())
for folder in ['armbian','boards','packaging','rootfs-overlay']:
 for f in (P/folder).rglob('*'):
  if f.is_file():copy(f)
for f in (P/'tools').iterdir():
 if f.is_file() and f.name not in excluded and f.suffix in {'.py','.sh','.ps1','.c','.inc','.js',''}:copy(f)
for f in (P/'docs').iterdir():
 if f.is_file() and (f.name.startswith('armbian-') or f.name in ['BOOT-BUILD-GUIDE.md','root-filesystem-growth.md','flash-f8-armbian-r1.md','ubuntu-driver-reuse.md']):
  copy(f)
  dst=R/f.relative_to(P);text=dst.read_text(encoding='utf-8-sig')
  text=text.replace('192.168.1.227','192.0.2.227').replace(r'C:\Users\LIKImk',r'C:\Users\YOUR_USER')
  dst.write_text(text,encoding='utf-8',newline='\n')
O=P/'outputs/armbian/f8-armbian-20261103-r2';D=R/'release/20261103-r2';D.mkdir(parents=True,exist_ok=True)
for name in ['manifest.json','privacy-audit.json','checks-summary.json','bundle.json','ZIP-SHA256.txt','SHA256SUMS','README-刷入说明.txt']:
 shutil.copyfile(O/name,D/name)
(R/'.gitignore').write_text('''/local/
/hardware/
/downloads/
/vendor/
/outputs/
/analysis/
**/__pycache__/
*.py[cod]
*.zip
*.zip.[0-9][0-9][0-9]
*.ext4.img
*.pem
*.key
.env
''',encoding='utf-8')
(R/'.gitattributes').write_text('''* text=auto eol=lf
*.py text eol=lf
*.sh text eol=lf
*.service text eol=lf
*.rules text eol=lf
*.conf text eol=lf
*.desktop text eol=lf
*.ko binary
*.ttf binary
armbian/rootfs-overlay/usr/bin/* binary
''',encoding='utf-8')
(R/'README.md').write_text('''# F8-PRO Armbian

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
''',encoding='utf-8')
(R/'THIRD_PARTY.md').write_text('''# 第三方来源与许可

各文件原有版权与许可证声明保持有效；本仓库没有为所有第三方文件统一重新授权。

- Armbian / Linux：使用 Armbian 的 RK35xx vendor 6.1.115 内核；Linux 驱动文件保留各自 SPDX/版权声明。内核与发行版不由本项目原创。上游：https://github.com/armbian/build 。精确整内核构建链仍待锁定，见 BOOT 构建说明。
- Fcitx5 与中文插件：Ubuntu 软件包提供。上游：https://github.com/fcitx/fcitx5 、https://github.com/fcitx/fcitx5-chinese-addons 。
- Fcitx5 OSK：上游 https://github.com/fortime/fcitx5-osk ，固定提交 `430feb3949b5721df4f37b7c559d52e28951c902`；F8 按键反馈补丁在 `armbian/fcitx5/patch-osk-haptic.py`。上游源码可按该提交获取；许可随覆盖层保留于 `armbian/rootfs-overlay/usr/share/licenses/fcitx5-osk/LICENSE`。
- Symbols Nerd Font 3.4.0：https://github.com/ryanoasis/nerd-fonts ，字体许可随覆盖层保留于 `armbian/rootfs-overlay/usr/share/licenses/f8-nerd-fonts-symbols/LICENSE`。
- GSL 触摸参考代码/固件、Rockchip 相机和其他厂商接口依赖：相关来源、参考版本和边界见 `armbian/touch/` 与对应适配文档；保留文件内原始声明。厂商二进制不意味着可由本项目额外授予许可。
- KDE Plasma、Mesa、Chromium、PipeWire 等发行版软件沿用各自的软件包版权与许可证，镜像内保留软件包版权资料。

缺少的构建依赖应从对应上游/发行版获取，不要把第三方二进制误认为本项目可独立重新授权的代码。
''',encoding='utf-8')
subprocess.run([sys.executable,str(P/'tools/audit-f8-github-source.py')],check=True)
