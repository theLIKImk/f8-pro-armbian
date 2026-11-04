# F8-PRO 触摸固件分派核验（2026-10-29）

原厂归档内核中，实际绑定驱动 gslX680_r8 对本机 compatible=gslX680_shuping 的静态分派选择了独立的 4,851 项固件。它与此前在 Image 中找到的通用 GSL3673_FW 不同。已提取板级参考数据并验证 AArch64 C 数组序列化；尚未接入新驱动或向控制器上传。

## 证据链与范围

真机只读查询确认内核 5.10.160、驱动 gslX680_r8、OF compatible=gslX680_shuping。对 GSL input 设备仅查询 EVIOCGABS 元数据，ABS_MT_POSITION_X/Y 范围分别为 0–800、0–1280；没有读取触摸事件流。报告为 analysis/armbian/touch-input-metadata.json。

tools/collect-f8-touch-symbol-offsets.py 只保存相对 _stext 的 58 项符号偏移，不保存实时内核地址，没有读内核内存。归档 Image 的 SHA256 为 90d648c1e4e47ce6b4a83415694fa9b4a7283465fa3749297d2078abb20bffa2。通过项目本地 [vmlinux-to-elf](https://github.com/marin-m/vmlinux-to-elf) 1.4.0（peewee 3.19.0）解出 71,364 个符号，并核对全部 58 项相对偏移；Image 头分支目标同时吻合 primary_entry/_stext。_stext 文件偏移为 65,536，不能直接当作文件零点。依赖仅安装在 tools/vendor-lib，没有全局安装。

tools/recover-f8-static-symbols.py 保存原始归档的符号与分析重定位副本；后者明确命名 relocated-ANALYSIS-ONLY.bin，不是启动产物。tools/disassemble-f8-touch.py 对原始 Image 做有界反汇编。tools/trace-f8-touch-descriptor.py 排除重定位表内的伪指针引用，tools/trace-f8-touch-firmware.py 继续验证注册指令、指针与长度。报告均位于 analysis/armbian/touch-static/。

可复核的文件偏移链如下（不是实时 RAM 地址）：

| 环节 | 文件偏移/结果 |
| --- | --- |
| r8 初始化函数 | 28786068；构造 descriptor 参数并调用 i2c_register_driver |
| i2c_driver 描述符 | 38433360；name=gslX680_r8，probe=21520308 |
| OF 表 | 23649512；每条 200 字节，compatible 位于 +64，data 位于 +192 |
| shuping 条目及 data | 23649712 → 23650504 |
| 固件 | 38433616；4851 × 8 = 38808 字节 |
| 算法初始配置 | 38510640；512 × 4 = 2048 字节，长度字段为 0x200 |
| 坐标上限配置 | data+24/+28 为 800/1280，与 input ioctl 结果吻合 |

probe 经 of_match_device 取条目 data 保存到设备私有结构；r8 的 gsl_load_fw 从该配置取得固件指针及项数。相邻 x702 条目选择另一份 4,521 项表，进一步说明不能因驱动名字相近而共用默认表。探针路径用配置中的 800/1280 设置 ABS_MT 坐标轴。物理面板 1200×1920 与触摸原始范围是不同层面的参数，后续需验证旋转及映射，不能直接把原始范围强改为面板分辨率。

## 已保存的参考数据

armbian/touch/reference-r8-shuping/ 包含原始固件/算法字节、C 头文件和 provenance.json。提取工具同时验证原 Image 字节与分析副本对应区间完全一致，避免把重定位改动混入配置。

| 数据 | SHA256 |
| --- | --- |
| 固件 38808 字节 | 60a271f6b8ba14e12d8b46c89892b31df8dbbe3c6037cba829fa2af378206809 |
| 算法 2048 字节 | 032de666c5e0ec4c8e6b8eacfd7a27559cb702071c08e4e0b1e128b287e643b8 |

tools/check-f8-touch-reference.sh 使用目标 gsl3673.h 的实际 struct fw_data 声明，以 GCC 14.2.0 交叉编译独立参考单元；sizeof=8，导出的固件和算法数据均与原始字节逐字节相同。结果见 reference-compile-check.json。这只验证结构布局与数据保真，不是完整驱动编译、算法兼容或硬件测试。

早先通用 GSL3673_FW 的完整匹配仍是有效的“原 Image 包含该表”证据；现在已确认它不是上述 shuping 静态路径选择的数据。没有读取运行中的算法内存或控制器固件，不能声称运行时可变算法配置未被修改。

## 后续适配

2026-10-29 第九轮更新：已生成独立候选 armbian/touch/candidate-r8-shuping/，加入 OF profile 数据选择、板级固件/算法、800×1280 坐标限制及原厂 GPIO 属性名；GPIO 初始化错误会中止 probe，板级候选不创建调试 proc 入口。保留通用 profile，专用 compatible 使用不同的评估名称，现有原厂节点不会自动绑定。147 个完整 32 字数据页静态校验通过。

候选完整 gsl3673.c 已在固定 6.1.172-f8-pro-armbian-eval 环境编译成 AArch64 可重定位对象，无编译诊断；源基线与固定源码一致，内嵌两数组与原始参考字节完全相同。compile-check.json 记录对象 SHA256。没有链接模块、启用节点或更改冻结四产物。该结果比独立数组编译前进一步，但仍不验证算法实现、IRQ、复位时序和 PM 的运行兼容性。原驱动使用的全局单例及生命周期也需要后续审查。

先审查并实现显式板级 profile：匹配名、GPIO 属性与极性、上电/复位及上传顺序、算法调用约定、坐标与 IRQ 报告、休眠恢复。目标通用驱动的 GSL,GSL3673、irq_gpio_number/rst_gpio_number、默认 2048×1536 与原厂均有差异，不能仅替换固件数组后启用。

新触摸节点仍 disabled；参考头文件只接入独立候选，未接入固定内核源码、已封装模块、rootfs 或启动包。现有四件评估产物未变，暂无可部署 FIT。下一轮继续核对算法、IRQ、复位/上传错误处理及 PM，再处理受控启动与硬件验证；继续保留原 Arch 恢复系统。
