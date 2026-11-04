# F8-PRO loader 与内存交接核对

2026-10-29 第十四轮更新：原厂 U-Boot payload 已找到并核验占位掩码/比较、guard 后改写及分配调用结构；不再只有默认字符串和公开参考推断。参考固定到 Rockchip 提交 1c535d65，旧分配函数与新版 FDT pad 行为有差异。详见 docs/armbian-loader-placeholder.md。实际环境、guard 身份/策略、最终 DT 扩容/内存修补仍未验证，boot_ready=false；下文为第七轮历史审查。

2026-10-29，纯本地只读归档审计，没有访问平板、生成候选FIT或修改U-Boot。

tools/audit-f8-loader-contract.py重新校验原始manifest列出的启动资产SHA256，以及原厂FIT内三个payload的SHA256和外置偏移边界。记录见analysis/armbian/loader-contract.json。此检查只证明归档完整性，不是RSA签名验证。

原厂FIT的FDT load为0xffffff00、kernel load/entry为0xffffff01，其字面payload范围不在旧运行DT观测DRAM内，不能当普通物理加载地址直接套用。历史ramdisk包装使用0xffffff02，但原厂Ubuntu FIT本次没有ramdisk条目。需要核对定制loader解释及实际重定位地址，不能只照抄字段。

归档U-Boot字符串版本为2017.09-230719-dirty，包含两份一致的内置环境默认值：kernel_addr_r=0x00400000、fdt_addr_r=0x08300000、ramdisk_addr_r=0x0a200000。它们只是编译进二进制的默认值，不能当成设备实际生效环境或内核入口交接日志。

原/新ARM64 Image的text_offset都为0、flags都为0xa，运行尺寸分别40,501,248和40,239,104字节。固定6.1.172的Documentation/arm64/booting.rst要求按运行image_size预留（含BSS），基址2MiB对齐；DTB为8字节对齐且不超过2MiB；kernel/initramfs需同处一个1GiB对齐、最多32GiB的窗口。头部相同不能证明新内核启动成功。

tools/check-f8-loader-layout.py完成8条合成测试：合法布局、kernel未对齐、运行内存重叠、DRAM空洞、保留区重叠、DTB未对齐、DTB超尺寸、initramfs窗口过宽。然后使用内置默认地址、旧观测banks与当前产物尺寸筛查，未发现几何错误。报告analysis/armbian/loader-layout-check.json仍明确实际地址/最终修补后DT尺寸/保留区完整覆盖/DT可缓存属性未验证，boot_ready=false。检查器不选择、设置或应用地址。

原厂DT的model为Rockchip RK3588S TABLET V11 Board，compatible为rockchip,rk3588s-tablet-f12-v11、rockchip,rk3588；当前编译包装明确为f8-pro,compile-check，其身份不等于整板DT。本轮完整固定源码目录仍未发现F12板文件，通用tablet-v11不能直接替代。原厂与草稿都没有静态DRAM节点，都保留3个零大小reserved-memory占位；新板还需证明loader的DRAM及保留区修补。

U-Boot归档中扫描到4个合法FDT候选（两种内容的重复副本），未找到/signature下公钥子节点。这既未证明实际使用的是哪个控制DT，也未证明熔丝/固件签名策略。上游[U-Boot签名文档](https://docs.u-boot.org/en/latest/usage/fit/signature.html)将required公钥策略放在控制FDT，不能仅看待启动FIT的signature节点；2017定制版实际实现仍需单独核对。

桥接助手本轮review已返回，见analysis/armbian/bridge-review/loader-contract-review.txt。其地址与DT证据建议作为核查清单采用；签名部分经主助手按上游文档修正，不直接按模型建议认定required位于镜像配置中。后续只向桥接发送必要地址/范围摘要，不发送完整运行DT。

下一步需要保存：实际loader解析/重定位证据，启动前最终DT的memory/reserved-memory及地址/尺寸摘要，控制DT与验签策略依据，以及受控交接的串口/早期日志。旧5.10改ramdisk启动通过不扩大为新6.1通过。整板供电、充电/USB-C/触摸及图形仍待适配，现有离线产物仍不可刷写。
