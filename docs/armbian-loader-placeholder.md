# 原厂 U-Boot 占位地址分支核验

第十五轮更新：已沿原厂二进制确认 signature/required/conf 判断结构、三个 FIT 属性对应环境变量，以及后续 boot_relocate_fdt 的 0x3000（12KiB）扩容。上一轮“最终扩容未知”已缩小；实际 fdt_high、原地扩容尾部容量和最终 memory 修补仍未知。详见下方新增记录。

2026-10-29，第十四轮；仅分析本地归档和公开源码，没有真机访问、内存/环境写入或生成候选 FIT。

Rockchip 官方 next-dev 参考固定到提交 1c535d65b8509f388d09e49fb6961f49fda35a1d，下载 15 个分析文件、240820 字节，来源与 SHA256 在 analysis/armbian/loader-source-reference/manifest.json。该提交不是已证明的本板固件源码。

[官方 fit.c](https://github.com/rockchip-linux/u-boot/blob/1c535d65b8509f388d09e49fb6961f49fda35a1d/arch/arm/mach-rockchip/fit.c) 将 `(addr & 0xffffff00) == 0xffffff00` 判作占位，fix_image_set_addr 在条件允许时改写 entry/load。前处理从 fdt_addr_r/kernel_addr_r/ramdisk_addr_r 取得地址；required=conf 的控制 FDT 策略会阻止占位改写。注意掩码只覆盖这些位，不能把它误写成对任意 64 位数的严格 32 位范围判断。

[官方 board.c](https://github.com/rockchip-linux/u-boot/blob/1c535d65b8509f388d09e49fb6961f49fda35a1d/arch/arm/mach-rockchip/board.c) 还可能根据环境布局、BL32/OP-TEE 内存改变地址。这进一步说明内置默认字符串不能代替生效地址。

## 原厂二进制对照

从归档 uboot.img 的 FIT /images/uboot 提取未压缩 ARM64 payload：容器偏移 0x1000、大小 1312056，静态 load=0x200000，SHA256 e6357ab74144e77790a71b39cd12746203dfb17a177889dcf19b9ec4e024a053。保存为 ANALYSIS-ONLY，不替换启动资产。

ARM64 logical-immediate 扫描找到 9 个掩码候选。多数属于无关的位运算，不能只因常量出现就命名函数；对照反汇编后，有效结构位于 payload 0x5998：

| payload 偏移 | 静态指令依据 |
| --- | --- |
| 0x599c / 0x59ac / 0x59b4 | old 参数 x2 与 0xffffff00 做 AND，再比较同一常量 |
| 0x59b8–0x59d0 | 非占位分支直接返回 0 |
| 0x59e0 / 0x59e4 | 调用 0x57b4 后，非零返回则跳过改写 |
| 0x59f0 | 获取默认配置子节点的对应调用结构 |
| 0x5a08 / 0x5a24 | 两处使用新地址的写入调用，与 entry/load 结构相符 |
| 0x5ab0 | 分配函数调用上述改写函数 |

tools/audit-f8-loader-fixup.py 验证确切指令和分支目标。guard 及两个写入 callee 的符号身份尚未独立完整证明，仍标注为源码结构对应，不能据此认定当前签名策略或实际执行结果。

旧分配函数随后直接将 payload size 按 512 字节向上对齐再分配，未见当前参考实现中的 FDT max-size+CONFIG_SYS_FDT_PAD 分支。这是明确的版本差异；后续 bootm 是否另行扩容 DTB 尚待查明，不能假定新版行为已经存在于本机。

证据目录 analysis/armbian/loader-placeholder/，报告 verified-fixup-structure.json；反汇编 fit-fixup-context.asm。记录的偏移属于归档 payload，不是真机重定位地址。

## 第十五轮：前处理、后续扩容及旧内核真机观测

分析工具 analyze-f8-loader-handoff.py 一次保存完整归档反汇编，并生成候选字符串引用；字符串扫描本身不作为数据流证明。audit-f8-loader-handoff.py 随后核对确切指令、寄存器和字符串地址：

- 0x57b4 函数在根节点查 signature，遍历子节点查询 required，再与 conf 比较。0x5998 的 guard 从 x18+224 取指针调用它。这确认静态策略逻辑，仍未确认当次使用的控制 FDT 或策略内容。
- 0x5ae8 前处理按 fdt→fdt_addr_r、kernel→kernel_addr_r、ramdisk→ramdisk_addr_r 调用分配/改写函数；地址读取为十六进制，缺省值 0 会被拒绝。
- 后续 0x2af4c 重定位函数明确加 0x3000；读取 fdt_high。全 1 值分支保留原位置并直接增大 totalsize，另一分支分配后调用与 fdt_open_into 对应的复制/展开函数。前一阶段未加 pad 不等于整个启动过程没有 pad；原地路径仍要求原缓冲区尾部确有空间。

布局检查已纳入额外 12KiB，新增“加 pad 后跨越 DRAM bank 末端”测试，共 9 条合成测试通过。按旧内存 banks 和内置默认地址筛查，加 pad 的新候选尺寸无几何错误；不是最终修补后 DT 或真实新内核交接证明。

本轮通过现有 SSH 只读查询 /proc/iomem 和 chosen/initrd 属性。当前 5.10.160 的 Kernel code 起点为 0x00400000，Kernel data 末端为 0x02aa0000（不含）；可见首尾跨度为 40501248，与原 Image runtime image_size 相符。initrd 区间为 [0x0a200000,0x0a9b4ae0)。起点与归档默认值吻合，这是旧启动链的实际观测，不能扩展为新 6.1 或生效环境内容已验证。没有读 RAM、U-Boot 环境、写设备或重启。

报告 verified-handoff-paths.json、loader-layout-check.json 和 live-loader-placement-2026-10-29.json。新内核地址、实际 fdt_high/控制 DT、原地容量及最终 memory/reserved-memory 修补仍待完成；boot_ready=false。

占位字段的解释已有原二进制依据，但生效环境、guard/控制 DT 策略、最终 DTB 空间及 memory/reserved-memory 修补、新内核运行内存保留均未完成。整板候选仍为编译检查 DT，不能直接启动。下一步定位前处理对环境和最终 DT 的使用，补齐可观测诊断通道和整板 DT，再准备受控启动；不把静态核验当启动成功。
