# F8-PRO Armbian BOOT 构建方法与接手说明

> **2026-11-02清理后：**旧构建及重现临时目录已删除，C4、重建所需C2固定输入、R1a BOOT和官方头文件/源码保留。旧完整R1包已删除；现存文件以outputs/README.md和analysis/build-cleanup/20261102/README.md为准。历史目录不存在时须使用新的工作目录重建，不恢复废弃C3或旧完整包。

更新：2026-11-01，供后续AI查阅。本说明依据当前脚本、已运行C4及独立目录复现结果整理。

## 1. 先明确“编译BOOT”是哪一条路线

**当前已经验证的路线是：复用官方Armbian内核Image，修改DTB／initramfs，再打包Rockchip FIT BOOT。** C1、C2、C4都沿用这条路线。日常设备树、启动脚本和模块加载时机适配通常不需要重编内核。

本项目的BOOT是以`d00dfeed`开头的FIT，包含外部数据段；不是Android boot.img格式。使用`mkimage`，不使用`mkbootimg`。

**重编整个Linux Image是另一件事，当前没有一条已经验证、可直接替换官方Image的完整源码构建路线。** 精确官方源码提交、构建补丁及完整配置还没有全部锁定。不要因目录名带kernel、版本看起来接近，就拿其中的Image替换当前内核。

## 2. 环境与路径

| 项目 | 当前值 |
|---|---|
| Windows工程 | `D:\Netdisk\杂项\F8-PRO\archlinux` |
| Windows另一访问路径 | `D:\Netdisk\Other\F8-PRO\archlinux` |
| WSL发行版 | `rg35xx-build`，构建用户root |
| WSL工程入口 | `/mnt/d/Netdisk/Other/F8-PRO/archlinux` |
| WSL构建暂存根 | `/var/tmp/f8-pro-armbian` |
| Python | 3.13.5 |
| mkimage | 2025.01 |
| dtc / fdtput | DTC 1.7.2 |
| ARM64语法检查 | `qemu-aarch64-static`，10.0.13 |

以上工具版本已在本轮实际读取。打包依赖Python标准库，以及`mkimage`、`dtc`、`fdtput`、`qemu-aarch64-static`。ARM64工具链仅在编译内核／模块／用户态C辅助库时需要，普通FIT重打包不需要交叉编译内核。

Windows PowerShell进入工程：

```powershell
Set-Location -LiteralPath 'D:\Netdisk\杂项\F8-PRO\archlinux'
```

WSL中执行工具时，从上述工程入口运行。Python脚本通过`__file__`定位工程，所以不要把构建脚本随便复制到`/tmp`后执行；这会改变其工程根目录判断。

## 3. 必须固定的输入与身份

| 输入 | 位置／身份 |
|---|---|
| C2完整BOOT | `outputs/armbian/official-f8-camera-c2/BOOT_ONLY_ARMBIAN_CAMERA_C2.img` |
| C2长度 | 49453272字节 |
| C2 SHA256 | `41b1f3f84f23107ee0de68a567406fa797de5436b65de6ab554acc538bb7247f` |
| 已验证C4 | `outputs/armbian/official-f8-camera-c4/BOOT_ONLY_ARMBIAN_CAMERA_C4.img` |
| C4长度 | 49453800字节 |
| C4 SHA256 | `fbbfa1ece55b3c62decbd10ae9c2ac98ed5d717dd5f8b941c49004deb6c0903a` |
| C2/C4共同内核 | `Linux version 6.1.115-vendor-rk35xx`，官方ArmbianImage |
| 内核长度 | 46561792字节 |
| 内核SHA256 | `a67daf71caefef6b97a22ba708bbb302b239a4a9b4874cadd17a217ebd0c37b7` |

**优先从已验证BOOT中按FIT字段提取kernel，不从一个仅仅同名的包目录取vmlinuz。** 本轮实查`/var/tmp/f8-pro-armbian/official-kernel/boot/vmlinuz-6.1.115-vendor-rk35xx`的哈希与上述Image不同。版本字符串相同不能替代文件身份校验。

`official-kernel/`的headers、System.map、配置及Module.symvers可用于已有验证路径的审计，但不能据此认定该目录任意同名文件均与当前Image配套。

## 4. 已验证的构建脚本及辅助代码

| 文件 | 用途 |
|---|---|
| `tools/build-f8-camera-c1.py` | 在S1基础上恢复原厂camera资源和graph的历史构建 |
| `tools/build-f8-camera-c2.py` | 修复共享MCLK归属、暂禁VCM的历史构建 |
| `tools/build-f8-camera-c4.py` | C2基础上的相机async等待链、提前加载修正；完整校验参考 |
| `tools/reproduce-f8-camera-c4.py` | 独立目录复现C4，并与已验证镜像逐字节比较 |
| `armbian/camera/boot-c4.its` | 从已验证FIT属性核对后的ITS，包含ramdisk的`os="linux"` |
| `armbian/camera/early-sensors-c4.sh` | C4插入initramfs的提前加载片段 |
| `tools/inspect_images.py` | FIT/FDT解析；本轮需要其中`fdt()` |
| `tools/f8_resource_image.py` | 严格解析／重写Rockchip resource中的DTB，保留两张logo |
| `tools/build-usb-bootlog.py` | 复用其中`cpio_read()`、`cpio_write()`，不要执行其旧主构建流程 |
| `analysis/armbian/live-memory-baseline.json` | 本板DRAM banks／保留区检查输入 |
| `tools/check-flash-file.py` | 本地镜像类型、分区容量、已知哈希检查；不访问平板 |

这些历史构建脚本不是任意板型的通用打包器；各自有固定输入哈希、版本标记及输出目录守卫。**不要删除旧preflight来强行重跑，也不要覆盖当前可回退镜像。**

## 5. 可直接复现的C4命令

当前新增的复现工具只在独立目录输出，不修改原C4、不访问设备、不刷写。它在内存中复用主构建脚本，仅更换输出目录、工作目录与输出文件名。

PowerShell示例：

```powershell
wsl -d rg35xx-build -u root -- bash -lc 'cd /mnt/d/Netdisk/Other/F8-PRO/archlinux && python3 tools/reproduce-f8-camera-c4.py --name camera-c4-repro-mycheck'
```

输出：

```text
outputs/armbian/official-f8-camera-c4-repro-mycheck/
  BOOT_ONLY_ARMBIAN_CAMERA_C4_REPRO.img
  preflight.json
  dt-change.json
  reproduction-check.json

/var/tmp/f8-pro-armbian/camera-c4-repro-mycheck/
  kernel
  fdt
  ramdisk
  resource
  boot.its
  init.sh
  busybox
```

名字必须满足`camera-c4-repro-`加安全的小写名字；再次运行换新名字，不覆盖完成的目录。若脚本报构建器文本已变化，应先审阅变化再更新复现工具的限定替换，不删除断言硬跑。

预期`reproduction-check.json`：

```json
{
  "result": "PASS",
  "byte_identical_to_verified_c4": true,
  "bytes": 49453800,
  "sha256": "fbbfa1ece55b3c62decbd10ae9c2ac98ed5d717dd5f8b941c49004deb6c0903a",
  "device_accessed": false,
  "original_image_modified": false,
  "original_preflight_modified": false
}
```

本轮已在`official-f8-camera-c4-repro-verified`和`official-f8-camera-c4-repro-guidecheck`完成同样的逐字节复现核验。无需为了验证构建命令再刷一次相同C4。

如果只想查看已有验证结果，读这两个目录的`reproduction-check.json`即可。原始C4构建器固定的输出目录已存在，直接执行`build-f8-camera-c4.py`会按设计拒绝覆盖。

## 6. 构建器内部顺序

### 6.1 提取并验证FIT的四个载荷

先用`fdt(blob)`解析BOOT。对`kernel`、`fdt`、`ramdisk`、`resource`分别读取：

```python
prop = fit['/images/' + name]
offset = int.from_bytes(prop['data-position'], 'big')
size = int.from_bytes(prop['data-size'], 'big')
payload = blob[offset:offset + size]
assert hashlib.sha256(payload).digest() == fit['/images/' + name + '/hash']['value']
```

这里的data-position按本项目外部数据FIT解释为镜像起点的绝对偏移。不要用猜测的固定偏移截取kernel，也不要把容器头当DTB。

普通设备树／init修改必须保持kernel逐字节不变，另外核对上节固定内核SHA256。基线输入不匹配就停下来查身份，不放宽断言。

### 6.2 修改DTB并限定差异

C4使用`fdtput`对原二进制DTB做小范围修改，再用解析后的完整字典与预先建立的expected比较。只允许计划内属性变化。

C4相对C2的DT变化仅有：

1. 在原有单个`initcall_blacklist`中追加`rkcif_clr_unready_dev,rkisp_clr_unready_dev`；保留`rockchip_cpufreq_driver_init`。
2. 新增`/chosen/f8-camera-async-trial = "c4"`。

保留`/chosen/f8-camera-trial = "c2"`，因为已安装的root服务以此作为启动守卫。也保留U5、BT1、S1标记及`f8_usb_u1=1`、`cpufreq.off=1`、root UUID和原native target。

不要新增第二个同名内核参数去赌解析顺序；不要恢复C1中两颗sensor独占同一MCLK引脚的冲突；不要把本板改回参考开发板的I2C6／DCPHY0摄像头接法。

C4保留C2的相机供电、pinctrl、clock consumers、VCM disabled及完整媒体graph。全量DTS反编译/重编译会带来额外变化；若采用这条路线，仍必须做同等严格的完整差异与phandle核对。

### 6.3 同步resource中的DTB

**FIT里的fdt和resource内的`rk-kernel.dtb`必须同步。**

```python
assert parse(original_resource)['rk-kernel.dtb'] == original_dtb
new_resource = replace_dtb(original_resource, new_dtb)
assert parse(new_resource)['rk-kernel.dtb'] == new_dtb
```

`f8_resource_image.py`验证RSCE表、512字节分块、范围和各条目的SHA1，并保留`logo.bmp`、`logo_kernel.bmp`内容。外层FIT还要重新计算整个resource的SHA256。不要只补一个DTB就忽略另一份。

### 6.4 修改initramfs

ramdisk载荷本身是gzip压缩的newc CPIO。用现有CPIO helper读取／写回；非计划修改的记录，其正文与权限、所有权等元数据应保持一致。

C4只在`init`中、原生root完成挂载校验且dev/proc/sys/run移动到root之后、执行systemd之前，插入`early-sensors-c4.sh`。它通过BusyBox chroot调用root中的官方gc5035/ov8858模块，每项有8秒超时，失败保留桌面启动流程。

两颗sensor的`.ko`来自当前native root；**不是把旧5.10模块塞进6.1内核**。该片段没有unbind、自动拍摄或供电寄存器改写。

重新打包前，必须对**解包后实际会执行的init**进行ARM64 BusyBox语法检查：

```text
qemu-aarch64-static <解出的busybox> sh -n <实际init>
qemu-aarch64-static <解出的busybox> --list
```

确认需要的`timeout`、`chroot`等applet确实存在。仅在主机bash执行`sh -n`不等于验证目标BusyBox支持所用语法／命令。

gzip使用`compresslevel=6, mtime=0`，避免gzip头中的时间造成不必要的不可复现差异。不要丢弃基线原有的USB、蓝牙、触摸等启动资产。

### 6.5 用固定ITS打包

实际命令在包含四个载荷的工作目录内执行：

```text
mkimage -E -p 0x800 -f boot.its <新输出镜像的绝对路径>
```

- `-E`把载荷放到外部数据区；`-p 0x800`沿用已验证布局。
- Python构建器将`SOURCE_DATE_EPOCH`设为基线FIT根节点的timestamp，以复现容器时间。
- ITS中的fdt/kernel/ramdisk load占位分别为`0xffffff00`、`0xffffff01`、`0xffffff02`；kernel entry也为`0xffffff01`。这是本板旧Rockchip U-Boot已核验的占位处理路线，不是实际物理RAM地址；不要照搬到别的bootloader。
- 保留四载荷的类型、arch、compression、load/entry、hash以及configuration引用。ramdisk的FIT compression仍为none，其数据内部已经是gzip CPIO。
- ITS中历史description带`NATIVE DESKTOP T1 NOT APPROVED`。本次为了精确复现保留该字符串；它是历史说明文字，不是当前实测结论或新的审批要求。

细节见`docs/armbian-loader-placeholder.md`。其中早期“尚未启动”的文字是历史阶段，当前C4已真机启动；但仍不能把本板地址规则推广成任意板型的通用保证。

## 7. 输出必须做哪些检查

构建成功仅说明工具执行结束。至少检查：

1. 从新FIT重新提取四个载荷，与工作目录内容逐字节比较，验证各SHA256。
2. 普通DT/init改动的kernel必须与基线逐字节一致，且匹配固定官方Image哈希。
3. FIT节点和属性集合完整比较，既检查新增／改值，也检查属性是否丢失；外部数据位置、大小和hash值可按新内容变化。
4. 完整DT限定差异；FIT和resource DTB一致；两张logo保持。
5. 解包实际ramdisk，核对只改了计划的CPIO记录，执行目标BusyBox检查。
6. 镜像小于boot的64MiB容量。沿用现有脚本对FDT所在bank和ramdisk所在bank做检查；FDT预留额外12KiB扩容。当前脚本校核位置为FDT `0x08300000`、ramdisk `0x0a200000`，以本板已建立的banks基线为依据，不能假设整段12GB连续可用。
7. Windows侧独立计算最终文件SHA256；保存preflight、差异说明和新版本号。

本轮独立复现时曾发现：四个载荷完全相同，但ITS少了ramdisk的`os=linux`，容器哈希因此不同。该次输出在`official-f8-camera-c4-repro/`，**不使用、不刷入**。已将ITS固定进工程，并把主构建器的FIT属性检查补为双向集合比较；后续两个独立复现目录才是PASS。这也说明只核对载荷哈希仍不够。

Windows独立校验示例：

```powershell
Get-FileHash -LiteralPath 'D:\Netdisk\杂项\F8-PRO\archlinux\outputs\armbian\official-f8-camera-c4\BOOT_ONLY_ARMBIAN_CAMERA_C4.img' -Algorithm SHA256
```

本地分区／哈希检查：

```powershell
wsl -d rg35xx-build -u root -- bash -lc 'cd /mnt/d/Netdisk/Other/F8-PRO/archlinux && python3 tools/check-flash-file.py --partition boot --image outputs/armbian/official-f8-camera-c4/BOOT_ONLY_ARMBIAN_CAMERA_C4.img'
```

此工具不会检查RKDevTool当前选中的文件、实机分区表或实际写入结果；输出中的这些字段是false。新版本不能仅为了消除报错就加入KNOWN，必须先完成上面的独立检查。与已验证C4逐字节相同的复现文件自然匹配同一已知哈希。

## 8. 真正需要重编Image时的门槛

以下是后续重编工作的前置条件，不是当前已验证的可运行配方：

- 锁定当前官方Image的精确源码提交、Armbian补丁、配置、工具链及构建身份。
- 在新O=输出目录建立原配置副本；修改目标配置后运行olddefconfig，并用diffconfig审阅全部差异。不能只看目标sensor从m变y，就忽略其它驱动被关闭。
- 对照kernelrelease、MODVERSIONS、System.map、Module.symvers和实际已用模块的导入CRC；核对CIF、ISP、Panthor、BCMDHD、显示和存储等关键驱动配置。
- 新Image与模块是配套构建结果。vermagic相同只是必要条件，不能证明结构体、内联代码、私有接口及全部ABI一致。
- 若只构建树外模块，modules_prepare在MODVERSIONS下不能自动替代匹配的完整Module.symvers。历史上个别模块经过逐项CRC／接口核对后可用，不等于整棵评估树能替代vendor内核。
- 新内核需要重新核对ARM64 Image头中的运行大小、内存布局、保留区和启动链，不能只比较文件长度。

**C3失败案例：**`kernel-config-build`是6.1.172评估树，不能拿来生成6.1.115 vendor替代Image。C3输出34300416字节的自建Image，缺失关键rkcif/rkisp/bcmdhd/panthor，真机不能启动。失败BOOT位于`outputs/armbian/official-f8-camera-c3/`，禁止刷入。详`docs/armbian-camera-c3-handoff.md`。

`linux-rockchip-config`中的85233a85b参考提交，以及另行下载的6.1.115/rkr5.1参考文件，均未被证明就是当前官方Image的精确构建来源；不要在交接时把“参考源码”写成“已匹配vendor源码”。

## 9. BOOT与native root必须分开交接

C4镜像自身不包含整个Armbian rootfs。root中的camera服务、官方sensor模块、IQ、RKAIQ、Python/Qt预览工具、音频UCM、USB服务和个人校准等不会因为重新打包BOOT自动获得。

当前C4的`/init`需要原native root `/dev/mmcblk0p6`，UUID `69056675-4a48-4006-a3f3-5132c00cc6f2`，并校验既有root标记和分区身份。这个固定UUID属于本机测试环境，不适合作为未经修改的通用安装包。

后续新BOOT必须保留已有root兼容的chosen守卫，或同步设计root更新；不能只改c4/c5标记就让现有服务被条件跳过。当前根文件`camera-start.py`已在摄像头后续测试中更新，BOOT原文件仍保持上述C4哈希。

## 10. 实机测试与当前状态

仅离线复现不需要刷机。真正产生新候选并需要实机测试时，现流程是用户用RKDevTool进入Loader，**仅写boot（p3），LBA `0x00008000`，容量64MiB**。不写Loader、不擦除、不重刷rootfs。当前C4可继续使用；C2为相机测试回退，S1为更早已验收基线。

启动后先用既有固定公钥SSH工具记录boot ID、chosen标记、内核身份、服务和media图，再做有界取帧。CIF/DPHY热unbind/rebind禁止：C1曾在rkcif_do_soft_reset触发NULL Oops。不要用热重绑代替新BOOT冷启动测试。

截至本次说明：

- 实机C4 boot ID：`532eb6df-13ce-4e63-9645-24d4136d96b9`，最后IP `192.0.2.227`。
- 双摄已取到真实帧；后摄已通过普通用户140帧14fps及Wayland预览176帧测试。
- 后摄3A的运行时修正是14fps派生IQ加不完整OTP拒用逻辑；都在root／相机进程中，不是新的BOOT变化。
- 用户确认后摄颜色正常、画面倒置；已把新预览程序默认旋转180°，保存画面使用相同方向。已经打开的旧程序需勾选旋转或重开后才使用新默认值。
- 前摄ISP30画质、后摄对焦、全分辨率拍照以及后续冷启动持久化仍待处理。不要将本说明或“BOOT可复现”当成摄像头全部验收完成。
- 本次文档与离线复现未访问／刷写／重启平板。用户此前打开的测试窗口按用户操作运行，不属于自动开机相机服务。

**接手顺序：先读HANDOFF/TODO最顶端最新状态，再读本说明；新增镜像用全新版本名和工作目录，保护已验证BOOT、root配置和个人校准。**
