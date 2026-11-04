# G1 黑屏、无日志盘：故障证据与 G2 修正

**实测更新：G2已通过GPU像素读回和内屏/限时Wayland窗口检查，系统running，触摸与充电仍未启用。详见[G2实测结果](armbian-official-g2-result.md)。下文保留修正前记录。**

2026-10-29。用户实测G1始终黑屏，没有USB日志盘；随后只刷回原BOOT。SSH已实际确认原Arch/5.10.160恢复。

## 已定位到的失败路径

恢复后读取/sys/fs/pstore，保存console-ramoops-0（64794字节）和dmesg-ramoops-0（67479字节）到local/hardware/armbian-official-g1-failure-20261029-01/。capture.json保存来源、大小和原始二进制SHA256；当前5.10 dmesg单独命名，不当成G1日志。没有删除或清空pstore。

G1持久化日志直接证明：

1. 官方内核6.1.115-vendor-rk35xx已经启动，实际DT model是F8-PRO图形候选。
2. initramfs已切换根，约37秒运行官方Ubuntu用户态systemd259.5-0ubuntu3，hostname=f8-pro-armbian。
3. 33.848197秒，regulator未使用清理关闭vdd_gpu_s0。
4. 41.751901秒，GPU电源域寻找gpu-supply，但设备树缺失。
5. 41.763609秒，Panthor模块注册期间，genpd在platform probe前尝试开启GPU电源域失败；41.764651秒触发panic_on_set_domain。栈包含rockchip_pd_power→genpd_attach→platform_probe→panthor_init。

所以boot-only方案确实已运行官方Armbian及尝试加载Panthor；这次不是“仍在Arch测试旧GPU”。黑屏/无盘由日志导出timer之前的内核panic解释，不是等得不够久，也不能据此认定G610/Panthor不兼容。实际EGL像素读回和KWin会话尚未开始。

VOP还报告vop-supply缺失并回退为不支持aclk DVFS；panel报告bpc=0。VOP/DSI已bind、rockchip DRM已注册，但这不证明屏幕输出成功。它们与GPU电源域panic分别记录，G2不混入这些非致命问题的猜测修改。

## 修正依据

上一版给Panthor节点设置mali-supply，但GPU电源域在Panthor probe之前就需要供电，缺少power-controller上的gpu-supply。较慢的镜像校验/切根让未使用regulator清理在模块接管前发生，暴露了这个启动次序问题。

实际官方6.1.115 Image/System.map调用位置验证：rockchip_pd_power中0x689198调用devm_regulator_get_optional，0x6891b0调用regulator_enable，之后0x6891e0才clk_bulk_enable。6.1.172参考源码另存并明确版本边界，其按genpd->name取得可选供电，在上电时先regulator_enable；不把参考源码冒称本次官方精确源码。

G2仅补：

`/power-management@fd8d8000/power-controller: gpu-supply = <F8 DCDC_REG1>`

与Panthor现有mali-supply指向同一个vdd_gpu_s0。不改550–950mV电压范围，不设置regulator-always-on，不关闭panic保护，不改变200MHz初测上限。model更新为G2。FDT差异检查确认除此两项没有其他设备树变化。

## G2 测试文件

outputs/armbian/official-f8-graphics-g2/BOOT_ONLY_ARMBIAN_26.8.1_GPU_G2_CANDIDATE.img

49427380字节，SHA256 **6afe593ffcdbeb5c1dbef48dc97b25caece51ac5de6f00288db57eba854c0f08**。

官方Image、resource、GPU/Wayland探针、匹配模块和2.15GB根镜像全部沿用G1。initramfs仅改变init/报告中的版本标识、USB序列号和空FAT卷标F8AG2；字节比较确认其余内容完全相同。shell/FAT/FIT四payload、回退布局含12KiB pad、GPU域引用读回验证通过。

恢复后再次只读重读设备上rootfs.squashfs，大小2148360192、SHA a6a76aef7feae1d1eb89c615ccbede837d7b4fc657c790580273ef5a20a6f5eb仍匹配，复用原文件，没有重新上传或覆盖。原始上传记录另存tablet-root-staging-initial.json。

只刷boot，起始0x00008000、大小0x00020000扇区，选G2。保持USB连接，等待3–4分钟，查看 **F8AG2**；观察屏幕是否亮、是否短暂出现Wayland测试窗口。其他步骤/范围沿用G1说明。G1保持原样保全，但标记为已失败，不再直接重测。

G2是有日志依据的修正候选，尚未真机确认。若仍无盘，回原BOOT后重新采集新的pstore；不要覆盖本次G1证据目录。充电/触摸仍禁用，日志保存后可回原BOOT正常使用。
