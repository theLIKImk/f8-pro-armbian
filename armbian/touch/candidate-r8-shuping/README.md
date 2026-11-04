# 未应用的触摸驱动候选

第十三轮：本驱动加入单实例 claim/devres release，全部关闭旧可写 proc；输入帧增加计数/ID/坐标/重复点及反馈写入错误检查，帧头使用非对齐小端读取。binding-input-check.json 记录绑定竞争/重绑及 17 个输入边界场景，模拟算法并非真实算法验证。单实例锁不覆盖其他 GSL 驱动的共享算法；整合时应排除同时使用。尚未整核链接或部署。

第十二轮：候选加入显示/系统两类 PM 原因与 mutex、F8 FB 错误重试、全槽位释放和 quiescing guard；pm-check.json 记录实际函数提取后的模拟验证。见 docs/armbian-touch-pm.md。通用路径仍保留原通知辅助层；Wayland/DRM 熄屏事件与真实硬件/内核并发未验证。

第十一轮：专用 profile 复位延时改为原厂静态推导的 20/10/10ms、startup 10ms；通用 profile 保持原值。模拟测试核对延时调用参数，不测量真实时钟/GPIO 波形。见 docs/ubuntu-driver-reuse.md 和 startup-contract.json。

第十轮更新：已改为同步上传，清寄存器/复位/固件/启动步骤逐级传递错误，完整传输计数检查与显式小端非对齐写入已加入；GPIO 延迟探测错误保留。FB 注册、IRQ 移除及 PM 恢复失败路径作局部修正。详见 docs/armbian-touch-transport.md。transport-check.json 记录 306 条成功写入比对及 1252 项模拟故障注入，compile-check.json 记录同版候选的驱动对象和内嵌数据检查；不代表真实硬件/并发验收。

本目录是对固定 6.1.172 gsl3673.c 的独立候选，不在已封装 Image、模块或 rootfs 中。用 tools/prepare-f8-touch-candidate.py 生成 gsl3673.c 与 profile.patch；参考头由 ../reference-r8-shuping/ 单独提供。编译脚本只复制到 WSL 独立目录并生成一个驱动对象，没有修改固定源码或部署。

候选按 OF match data 选择固件、算法初值、坐标范围和 GPIO 属性。专用匹配名为 f8-pro,gslx680-shuping-eval，与现有 gslX680_shuping 不同；现有禁用节点不会自动匹配。原 GSL,GSL3673 继续选通用配置。板级候选不创建可写调试 proc 入口；GPIO 初始化失败会停止 probe，避免原函数返回错误后仍继续初始化/上传。

compile-check.json 记录 AArch64 完整驱动对象编译及其内嵌两数组的逐字节检查。尚未链接模块或验证算法实现兼容性、IRQ/复位、休眠恢复和实际触摸；原驱动的全局单例与其他生命周期问题也未全面处理。没有可用的完整触摸移植成果，不能启用或刷写。

上传表已静态确认由 147 个完整页组成，每页一条 0xf0 页选择和 32 个连续 u32，符合继承上传循环的分批结构；该检查不等于 I2C 上传成功或错误处理完整。DT 中历史 screen_max_x/y=1200/1920 原样保留作原厂证据，候选 profile 的 input 原始范围为 800/1280。物理屏幕映射留待 Wayland 真机验证。
