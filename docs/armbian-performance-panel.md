# F8 性能控制与 CPU P2A（2026-11-02）

> 最终频率策略已更新：GPU已实测并开放200–1000MHz，CPU使用内核当次PVTM校准表（小核型号边界1800、大核2400MHz），不再固定旧2256上限。P3启动下自动恢复完整调频；旧BOOT的手动启用路径保留。详 [P3实机及动态分档修正](armbian-full-performance-p3.md)。

> 最新P3更新：CPU已接入完整Rockchip OPP并开放到本机校准上限，小核1800MHz、大核2256MHz；面板已同步。GPU1000MHz BOOT已生成待刷，当前GPU仍400MHz。新P3启动marker下加入延迟CPU自动加载，P2A回退仍跳过。详 [全性能P3](armbian-full-performance-p3.md)，下方保留此前P2A阶段记录。

## 当前验收结果

用户确认 CPU P2A 启动成功；实查 boot_id `8bf8449c-1203-414b-886e-421078079271`，marker `p2-fixedvolt-1200mhz`，cpufreq.off 为0，default_governor powersave，vendor及cpufreq-dt平台初始化黑名单保留。随后手动加载独立模块成功，三个policy分别覆盖0–3/4–5/6–7，三个CPU cooling device max_state均2。

逐集群、逐档短测816/1008/1200MHz成功，SCMI时钟及scaling_cur_freq与请求一致。小核750mV、大核800mV测试前后及每次采样保持，最高soc47.153°C，无Oops/BUG/锁死记录。相同2秒整数循环的吞吐1200MHz比816MHz约提升43%（小核）和51%/52%（两组大核）；仅是短时单核循环，未测长稳、全核持续负载或完整应用。

随后 ondemand 自动调频测试三集群均观察到负载升频，已保持816–1200MHz自动调频。GPU保持200–400MHz simple_ondemand，既有P1短测terrain22→50FPS。

面板已安装、打开并经过用户实际操作验收：“都正常，能固定并恢复自动”。包含触摸、Polkit管理员认证、GPU固定300MHz及恢复自动。无需再重复要求相同验收。

证据：`local/hardware/cpu-p2-start01.json`、`cpu-p2-load01.json`、`cpu-p2-frequencies01.json`、`cpu-p2-auto01.json`、`performance-panel-install02.json`、`performance-panel-live01.json`；界面渲染 `analysis/linux-issues-20261102/performance-panel.png`。

## 面板用法与边界

应用菜单“F8 性能控制”；当前用户桌面 `F8-Performance.desktop`。GPU、小核、两组大核各有一张卡，显示当前频率/范围/温度，支持自动、手动范围、固定目标和全部恢复自动。横屏双列、窄屏单列，可滚动。打开界面只读，应用时经pkexec正常认证；没有sudo免密规则。

当前仅开放 GPU200/300/400MHz、CPU816/1008/1200MHz。用户提供的GPU1000MHz、A76 2400MHz、A55 1800MHz已作为后续适配目标显示，尚未解除限制。更高频率涉及完整供电/OPP/PVTM/read-margin/DSU适配，不能靠面板直接填写或拉高。

调整只作用于本次启动，不写开机频率配置。CPU试验模块仍不自动加载；重启到P2A后若CPU卡尚不可调，点“启用本次CPU调频”可认证后加载已校验模块并启用自动。该路径有marker、核心开关、模块SHA/权限、三策略完整性检查；目前“无策略到加载”的根模块路径已人工实测，面板此按钮的完整冷启动流程尚未再测。若启动的是P1/R1a，不会绕过其cpufreq.off保护。

固定目标通过标准sysfs最小/最大频率限制实现，仍受内核温控约束，不禁用cooling、不写寄存器或PMIC。CPU驱动只有保守固定供电范围，不是完整vendor DVFS；长稳、休眠/热插拔、开机自动加载及额定最高频率仍待适配。

## 实现与打包

- `armbian/power/performance-panel.py`：普通用户PyQt6 Wayland GUI。
- `performance_state.py`：只读sysfs、受保护的已验证档位清单。
- `performance-apply.py`：root所有的隔离Python助手，仅接受固定设备ID和已开放频率；按安全顺序改范围，失败尝试恢复原配置，锁防并发。
- `performance-limits.json`：GPU400/CPU1200MHz上限及CPU模块SHA，部署于 `/etc/f8-pro/`，root:root0644；普通用户不能提高它。
- `org.f8pro.performance.policy`：标准auth_admin/auth_admin_keep，无身份白名单、无全放行。
- `f8-performance.desktop`：菜单/桌面入口。

部署工具 `tools/prepare-f8-performance-panel.py`，根安装器生成在local/hardware并经现有SSH工具执行。源根fs配置脚本已加入上述文件、校验后复制CPU模块和新用户桌面入口；尚未重建干净完整ROOTFS包，后续包必须明确BOOT是否为P2A，不能假定旧C4 BOOT开放CPU调频。

验证包括5项自动测试（未验证频率/错误单位/倒置范围/固定模式、策略缺失、部分失败回滚）、真实设备GPU300MHz及CPU1008MHz固定/恢复、拒绝GPU1GHz且范围不变、4卡真实Wayland界面渲染、用户认证操作验收。全部设备已恢复自动。
