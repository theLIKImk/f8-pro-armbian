# F8-PRO RK806管脚、关机及eMMC适配

> 最新需求：仅使用 KDE Plasma Wayland；原生 X11 双会话要求已取消。相关旧版本约束与X11验收步骤不再执行。


2026-10-28。仅本地源码检查和编译，没有真机电源或存储操作。

## RK806目标实现

锁定目标drivers/mfd/rk806-core.c明确查找default、pmic-power-off、pmic-sleep、pmic-reset、pmic-dvs状态；drivers/pinctrl/pinctrl-rk806.c优先从PMIC子节点pinctrl_rk806取内部管脚定义，支持gpio_pwrctrl1/2/3和pin_fun0至pin_fun5。

新增f8-pro-pmic-pins.dtsi，原样迁移原厂16个内部管脚状态和default/power-off引用。原厂dvs1_null与dvs2_null同指gpio_pwrctrl2且同为pin_fun0；保留原值，不猜测更正，也不能将此认定为所有管脚初始化已正确。没有添加原厂未选择的pmic-sleep状态。

目标rk806-regulator.c的shutdown回调在SYSTEM_POWER_OFF时配置关机序列和PWRCTRL功能；shutown_by_pwrctrln（上游属性名如此拼写）缺省为1。rk806-core.c虽然查找power-off状态，但在已审查的core/SPI/regulator文件中未发现选择该状态的调用。因此仅恢复状态定义不等于关机动作完全适配，仍需检查平台关机/固件链并在准备恢复方案后实测。

目标RK806 core suspend/resume处理IRQ唤醒，regulator的PM回调另处理电压选择和DVS。原厂休眠策略不能仅凭驱动存在复制为完成；rockchip_suspend继续disabled。

## eMMC

新增f8-pro-storage.dtsi：8位总线、non-removable、no-sd/no-sdio、HS200 1.8V、最大150MHz，均来自原厂。目标SoC默认max-frequency为200MHz且有supports-cqe，草稿降回150MHz并删除CQE，不引入HS400。此为待测试配置，不代表已在候选内核上验证读写或稳定性。

基础配置文本中已确认MMC、SDHCI平台/DWCMSHC、Rockchip SPI、RK806 SPI/pinctrl/regulator、ext4和initramfs相关主要支持；最终内核仍须经配置合并/olddefconfig核查，包含MMC_BLOCK、GPT识别、压缩格式及固件需求。当前下载的是配置输入，不能代替最终.config。

不写chosen/root启动参数，不修改GPT或现有PARTUUID，不绑定新rootfs至当前根分区。启动包装、loader对新内核的支持、DRAM/保留内存、CPU供电及GPU节点互斥尚未完成，编译DTB仍标注DO-NOT-FLASH。

## 验证结果

集成编译通过，223项原厂属性比对通过，无新增警告。新增检查覆盖eMMC参数/CQE禁用、所有原厂PMIC内部管脚pins/function、default和power-off的引用。状态定义仅证明被编译进DTB，不能证明驱动实际执行或硬件功能通过。

下一阶段先核对CPU/GPU/内存供电和保留内存，再完善板级启动配置及测试rootfs。触摸兼容、无线及其余硬件依然需要适配，尚未构建或部署完整Armbian系统。
