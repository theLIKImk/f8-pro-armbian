# F8-PRO 显示路由适配

2026-10-28。本轮仅核对原厂证据并本地编译，未访问或修改真机。

## 确认的硬件路径

原厂 display-subsystem/route/route-dsi0 的 connect=0x38，对应 /vop@fdd90000/ports/port@2/endpoint@3，即 VP2→DSI0。DSI0 的 VP2 输入为 okay，VP3 输入 disabled。候选 rk3588s.dtsi 的默认 connect 指向 VP3，不能直接使用。

新增 armbian/dts/f8-pro-display-route.dtsi：显式指定 vp2_out_dsi0，启用 VP2 输入端点、禁用 VP3 输入端点；DSI host 与 route 仍disabled，等待整板电源/驱动验证。面板、电源、背光也保持禁用。

真实 PHY 为 /phy@feda0000，在目标源码中标签为 mipidcphy0。相似的 mipi_dcphy0 与 mipi_dcphy1 是 /mipi-dcphy-dummy 的兼容标签，不可用来配置真实PHY。目标 DSI0 默认也已经引用真实 mipidcphy0，草稿显式写出以便审查。真实PHY保持与原厂相同的okay状态，但不代表已经完成显示功能验收。

## 验证方式

tools/validate-armbian-peripheral-dt.py 使用fdtget检查原厂与草稿的route目标、DSI输入和VOP输出的双向连接、PHY引用及DSI输出到面板的双向连接。按目标路径比较，避免不同DTB数值phandle变化造成误判。还检查VP2/VP3输入状态与原厂一致，并确保草稿route/host没有启用。

完整结果在 analysis/armbian/dt-validation/validation.json。原有177项电源/外设/面板参数检查继续执行。

## 尚待处理

VOP的状态、IOMMU、plane分配、电源域和时钟源需要结合目标驱动核对。原厂VP2 plane-mask=0x140、primary-plane=8；目标SoC基础文件未直接配置这些板级字段，不把旧数值盲目套入新驱动。还需检查单RK806的pinctrl/关机行为和电源消费者，以及显示PHY共享摄像头资源的关系。

目前仍是编译检查包装，缺少完整启动、内存、存储和GPU/用户空间集成。DTB标有DO-NOT-FLASH；没有亮屏、GPU导入、触摸或休眠功能测试。

本轮结果：177项属性一致，4项路由/PHY引用及面板双向链接通过，新增警告0。
