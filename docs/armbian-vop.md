# F8-PRO VOP2 图层和依赖审计

2026-10-28。依据锁定的 Armbian linux-rockchip 提交，未修改或启动真机。

## 图层能力核对

目标 rockchip_vop.h 定义 Cluster0/1/2/3 和 Esmart0/1/2/3 的物理编号。rockchip_drm_vop2.c 的 plane_mask_check 要求主图层包含在掩码内、每个物理图层仅分配一次、全部物理图层均覆盖，且符合窗口 possible_vp_mask。

工具 tools/audit-f8-vop-planes.py 解析目标 RK3588 专属窗口表，验证原厂四个VP配置：

| VP | 原掩码 | 物理图层 | 主图层 |
| --- | --- | --- | --- |
| 0 | 0x005 | Cluster0、Esmart0 | Esmart0 |
| 1 | 0x00a | Cluster1、Esmart1 | Esmart1 |
| 2 | 0x140 | Cluster2、Esmart2 | Esmart2 |
| 3 | 0x280 | Cluster3、Esmart3 | Esmart3 |

静态约束检查通过。生成 armbian/dts/f8-pro-vop.dtsi，采用目标命名常量表达掩码及主图层。该工具依赖当前下载的头文件/驱动和归档原厂DTS，尚未做运行时DRM测试。详细结果 analysis/armbian/vop-plane-audit.json。

## IOMMU 与电源域

原厂 VOP 引用 /iommu@fdd97e00 和 RK3588 VOP 电源域，目标 SoC 定义对应 vop_mmu 与 power/RK3588_PD_VOP。草稿显式引用上述节点，验证器分别解析原厂和草稿的phandle再比较目标路径与电源域编号，不直接比较不稳定的phandle数值。

VOP与IOMMU暂时disabled，显示route/host仍disabled。目标VOP驱动比原厂增加时钟和工作频率策略，继续使用目标SoC的驱动配套时钟定义，未将旧clock列表覆盖新定义。750MHz assigned-clock与目标内核多模式频率/OPP策略的运行行为仍需后续验证。

## PMIC 尚存差异

SoC侧pmic_pins的7组管脚与原厂文本对应；但原厂RK806子pinctrl及pmic-power-off状态不在目标通用单PMIC文件中。原厂dvs1_null与dvs2_null都指向gpio_pwrctrl2，这一重复必须结合目标RK806 pinctrl实现及关机流程核查，不能据此猜测修正管脚。电源轨约束通过不等于关机/休眠适配完成。

## 验证范围

集成编译工具继续检查原有177项参数，并新增8项VP掩码/主图层读回、IOMMU与电源域引用及禁用状态检查。结果在 analysis/armbian/dt-validation/validation.json。草稿仍不是完整板级DTB，没有写入设备。

下一步：核对RK806子pinctrl、关机回调与休眠状态；检查存储和内核启动依赖，再形成完整板级配置与恢复方案。GPU节点互斥、固件与Armbian根文件系统仍待集成。

本轮结果：集成编译通过，185项参数一致，IOMMU/电源域检查通过，新增警告0。
