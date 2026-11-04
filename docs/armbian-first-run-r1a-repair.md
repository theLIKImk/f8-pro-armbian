# R1a：首次账户创建修复与rootfs扩容（2026-11-02）

> 最新实机覆盖下方待刷状态：用户已成功创建并登录likimk，SSH核验根文件系统已到246960619520字节。f8setup延后清理已完成，AccountsService仅剩新用户。另发现原R1镜像Netplan残留Wi-Fi配置，旧包须保持私用并另版重包；详[清理及Netplan记录](armbian-setup-cleanup-and-netplan.md)。

用户已刷入R1并启动到向导，点击完成后出现旧helper通用错误：“设置未完成，已保留向导入口。请重试；若仍失败，请保留当前界面。”随后报告256GB空间未全部可用。**当前不再是旧f8test测试系统**；新包SSH默认关闭，不要绕过主机密钥验证或沿用旧SSH自动脚本。

## 已复现缺陷与修复

旧helper先 `useradd -m`，再用 `shutil.copytree(..., symlinks=True, dirs_exist_ok=True)` 复制skel。真实useradd若已正确复制skel中的服务链接，copytree会因目标链接已存在抛出shutil.Error；dirs_exist_ok并不允许重复创建已有符号链接。已在独立目录复现。之前QEMU环境的useradd没有完整复制隐藏文件，因此离线测试漏过这条实际路径，这是测试覆盖缺口。

新helper改 `useradd -M`，只由Python复制一次受控skel，家目录0750、所有权归新账户；如用户名对应目录已存在则拒绝并保留，不覆盖数据。增加操作阶段/异常类型提示，不输出密码或命令stdin/stderr。实机原始具体异常日志尚未读取，因此本补丁修复了确定存在、可触发同一错误的缺陷，**是否就是该次实机失败原因仍以刷入后重试结果为准**。

- 原helper SHA `4e6b521190ebbc65e7077eb622f02e807f61a68561f11acade8142e2244e5108`。
- 新helper SHA `082b2fb3165496c59357720dd8ca4257cee84273a80ef1f6b7e845d7f831f289`。
- 五组Linux回归测试通过，模拟真实useradd预复制，覆盖链接、失败清理/重试及已有目录不覆盖。
- 更新helper后离线ARM64真实账户创建/密码/默认配置/两种登录配置测试再通过，记录 `/var/tmp/f8-pro-armbian/release-r1/first-run-native-test-r1a.json`。未在实机执行新helper。
- 补做QEMU chroot真实sudo入口探针得到effective uid非0；这是QEMU用户模式不能模拟setuid语义的限制，不能当作实机sudo配置失败的证据。用户收到helper自己的JSON错误，说明实机该次已进入helper。

## 256GB与12GiB的区别

R1写入的是12GiB ext4文件系统，没有自动扩到原分区大小。刷入镜像不等于重新格式化整块存储，剩余容量通常仍位于原p6分区内。R1a安装独立root扩容服务，**不格式化、不改GPT、不改其他分区**。

服务等SDDM启动后再运行，保留C4相机早期加载时序；只有以下条件全部匹配才执行在线resize2fs：F8-PRO模型、R1根标记、实际根为/dev/mmcblk0p6/ext4、文件系统UUID69056675-4a48-4006-a3f3-5132c00cc6f2、PARTUUID614e0000-0000-4b53-8000-1d28000054a9、起始0x78000、482344960个512字节扇区、4KiB块、无ext4错误、现有文件系统不大于分区。

预期p6为246,960,619,520字节（约247GB/230GiB），这是原分区可用总大小，不等于厂商标称256GB整盘；其他原有系统分区保持。实际已扩容则不重复操作。几何或身份不同会拒绝扩容，不盲用固定命令。两组计划测试验证目标/无需扩容及所有身份/尺寸/错误计数拒绝条件；**新系统实际扩容仍待刷入验证**。

安装 `/usr/local/lib/f8-pro/root-grow-r1a.py`、`/etc/systemd/system/f8-root-grow-r1a.service`，启用到f8-desktop.target.wants。状态与resize日志保存 `/var/lib/f8-pro/root-grow-r1a/`；新账户登录后可用sudo检查。脚本不主动修改保留块比例。扩容改变根文件系统尺寸，不改变分区表。

## 仅刷BOOT

文件：`outputs/armbian/f8-first-run-r1a/BOOT_ONLY_F8_ARMBIAN_R1A_SETUP_GROW.img`，49,459,328字节，SHA256 `2a4901174382cbb8e0387f8de0220c8bebfff2fb830ca7d6aac5dd7794cb75dd`。

1. 进入Loader，RKDevTool“下载镜像”只勾 **boot / 0x00008000**，选择上述文件。
2. **不勾rootfs，不格式化，不擦除，不改分区表**。启动时按旧/新helper哈希守卫更新代码，并安装延后扩容服务。
3. 重启后重新填写向导并提交。设置成功后进入登录界面，使用新账户登录；然后查看根文件系统容量。如果仍失败，回复新提示里的具体阶段和错误类型，不提供密码。

BOOT以原C4为输入，仅改ramdisk安装段及新增三个资产；kernel/DT/resource逐字节不变，保护CPU/USB/相机等既有配置。对非R1根跳过；已有不同版本helper拒绝覆盖。旧helper备份在 `/var/lib/f8-pro/first-run/helper-before-r1a.py`。重复启动安装幂等；刷回C4不会自动撤销已写入root的helper或撤销扩容。

离线FIT哈希、内存、容量、实际打包ARM64 BusyBox shell语法检查通过；从最终镜像提取安装段，在ARM64 BusyBox隔离chroot执行首次/重复安装、未知helper拒绝、非R1跳过均通过。Windows原始BOOT完整哈希/容量/格式检查通过。证据 `preflight.json`、`packed-install-test.json`、`windows-boot-check.json`。**尚未刷入，未宣称账户或扩容实机验收通过。**

原R1 ZIP和ROOTFS保持原字节及原校验值，但带旧向导缺陷且未自动扩容；新部署须配R1a BOOT，不再推荐原ZIP中的C4 BOOT单独配该ROOTFS。完整新版本重包应另建版本，不能覆盖已完成的R1归档。
