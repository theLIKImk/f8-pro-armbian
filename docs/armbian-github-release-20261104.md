# GitHub 公开发布记录 · 2026-11-04

仓库：https://github.com/theLIKImk/f8-pro-armbian

测试版 Release：https://github.com/theLIKImk/f8-pro-armbian/releases/tag/v2026.11.03-r2

2026-11-03 R2 完整 BOOT＋ROOTFS ZIP 已按 GitHub 单附件限制拆为三个连续分卷，全部上传。原包 5,051,101,732 字节，SHA-256：b6a2acc525a31a12df98a00c1d9364f60d29a9a1de02080bb8bfe9bef20212a8。

下载全部分卷、split-manifest.json 和 merge-release.py 到同一目录，运行 python merge-release.py；逐卷及合并后的 ZIP 均检查 SHA-256，之后再解压。不要单独解压分卷。分卷是对原 ZIP 的按字节拆分，没有重新生成镜像。

Release 共12个附件，均已比对 GitHub 返回的大小和 SHA-256。独立、不带认证的公开 API 检查通过，split-manifest.json 的公开下载与内容哈希通过。标签实际指向 ec1eaacb277943974ddc81555374f7ef713348ce；后续上传工具和文档的维护提交在 main。

仓库公开了适配源码、覆盖层、构建/安装工具、技术文档及发布清单。排除本机 local/hardware/downloads/vendor/analysis/outputs 数据、原始日志和6个旧密码测试脚本；公开目录凭据模式扫描通过，没有上传本次认证 Token。临时认证只经 stdin/内存传给进程，未写入 remote URL、Git配置或凭据文件。

镜像原有隐私审计保持通过：Wi-Fi连接/密码、SSH主机及用户密钥/known_hosts、旧账户和个人home已清除，SSH默认关闭。云拼音默认百度，可在Fcitx5设置中关闭。本次没有修改或刷写平板，也没有进行新刷/冷启动验收。

本地证据：local/github-publish-20261104/public-verification.json、source-audit.json、source-pushed.json、published.json；Release 分卷及合并脚本在同目录 release-assets/。公开验证摘要也保存于仓库 release/20261103-r2/public-upload-verification.json。

上传采用三个分卷并行，全部通过后才公开测试版。GitHub 的草稿按标签查询可能返回404，恢复任务应使用草稿ID或列表查询；本轮遗留的旧草稿已删除，未修改其他发布版本。工具已加入稳定ID恢复、并行上传及发布后URL刷新逻辑。

硬件限制和刷入说明仍以 armbian-release-20261103-r2.md 为准；这次上传不代表电池、多指触摸或相机高级功能新增验收。
