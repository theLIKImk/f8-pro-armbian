# 触摸候选：休眠协调与触点释放

2026-10-29，第十二轮。所有修改仅在独立触摸候选，未部署或改动平板。

## 修改

原目标 tp_suspend.h 在 FB unblank 回调中忽略恢复返回值，并在调用前更新状态；恢复失败后，相同 unblank 事件可能被缓存状态过滤。原驱动休眠的触点清理又受未启用的 SLEEP_CLEAR_POINT 控制，该旧分支还包含一次模拟按压，不能直接打开宏解决。

候选将屏幕 blank 与系统 sleep 分为两个原因，使用每设备 state_lock 串行处理。任一原因仍存在时保持休眠；两者都解除后才恢复。操作失败回滚对应原因，恢复失败保持 IRQ 静默并拉低复位，后续相同事件可再次尝试。未标记恢复成功前不启用 IRQ。

本板评估 profile 使用独立 FB notifier，不再通过原 tp_suspend 辅助层缓存状态；错误通过 notifier_from_errno 返回，注册失败会释放 IRQ 并清理 workqueue。通用 profile 的通知注册接口仍保留。F8 是 DSI 平板，此候选没有注册辅助层的 EBC 通知，未主张适用于电子墨水屏。

休眠先设置 quiescing，禁止完成中的输入 work 重新启用 IRQ；随后禁用并同步 IRQ、排空 work，再释放全部 11 个已分配槽位（包括槽位 0）并清理跟踪/滤波历史。不生成模拟触点。恢复检查成功后才清除 quiescing。remove 的 stopping 与 PM 锁协调，避免状态转换与移除标记同时修改。

实现位于 armbian/touch/templates/f8-pm-block.c，由 prepare-f8-touch-candidate.py 插入候选。没有修改冻结的目标源码或配置。

## 验证及范围

tools/test-f8-touch-pm.py 提取实际候选函数，用主机 pthread mutex、模拟 IRQ/输入设备/寄存器步骤运行；UBSan 通过。覆盖：

- 屏幕先睡、系统后睡，以及系统先睡、屏幕后睡；仅解除一个原因不会提前恢复。
- 重复休眠不会重复断电或释放；11 个槽位及历史状态清空，没有虚假按压。
- reset/startup/memory-check 三阶段失败，保持非激活与 IRQ 禁用，随后重试成功。
- 非 blank/空事件忽略；FB 恢复失败正确返回错误，相同 unblank 事件可重试。
- 排空 work 时模拟 worker 完成，quiescing 阻止重新启用 IRQ；stopping 同样阻止。
- 两个线程合计 4000 次显示/系统 PM 请求，结束状态正确；模拟恢复步骤断言没有仍存在的休眠原因。

完整候选另经 AArch64 6.1.172 对象编译及内嵌数据核验；传输序列测试继续覆盖 306 条成功写入、12 段标称等待及 1252 次故障注入。报告 pm-check.json、compile-check.json、transport-check.json 均位于候选目录，必须对应相同 candidate_sha256。

这些测试没有运行真实内核调度器、IRQ、GPIO、算法或控制器，也不证明所有内核并发路径安全。4,000 次线程请求是主机压力检查，不是内核竞态证明。FB blank 是否由当前 Wayland/DRM 显示栈在实际熄屏时发出，仍需另行验证；system PM 路径也没有真机运行。

## 下一步

处理遗留的全局单例/算法共享与绑定生命周期，核对输入帧、控制器状态及原厂算法行为，再做候选整合。真实 GPIO/供电、内屏/GPU 与整板 loader 前置条件未完成，触摸 DT 仍 disabled，四件封装评估产物保持原版本，不生成部署 FIT。
