# 触摸候选：同步上传与传输错误处理

2026-10-29，第十轮。修改仅位于 armbian/touch/candidate-r8-shuping/ 独立候选；固定内核、封装产物、设备树启用状态及平板均未改动。

## 修正的问题

原目标驱动的 init_chip 只调度下载 work 就返回成功，probe 可在上传完成前请求 IRQ 并标记设备激活。下载 worker 中的清寄存器、复位、上传和启动操作忽略传输错误；test_i2c 用计数器处理错误，短读写也可能被当作成功。这会使初始化结果不能反映上传是否完成。

候选改为同步 gsl_program_chip，按原顺序和延时执行 clr_reg→reset→load_fw→startup→reset→startup；每一步失败立即返回。probe 收到错误后清理输入 workqueue，恢复路径在失败时保留 IRQ 禁用状态，不标记激活；系统 PM 的待恢复标记只在恢复成功后清除。没有保留异步下载 work。

底层完整消息/字节数才算成功；负 errno 原样返回，短正返回值转换为 -EIO。固件写入函数返回 int 并逐批检查结果，fw2buf 改为 put_unaligned_le32，避免把 buf+1 强转成 u32 指针。内存状态读失败直接返回，不能把读失败误当作固件标志失配再启动恢复上传。

GPIO 获取错误保留 -EPROBE_DEFER 等原返回值，请求及设置方向的错误逐级返回，GPIO 0/1 不再被有效性检查误排除。OF GPIO flags 使用正确的枚举类型，不作为 IRQ trigger flags 解释。原厂 r8 probe 的 request_threaded_irq 静态指令确认 flags=1、thread_fn=NULL，报告 analysis/armbian/touch-static/irq-request.json；这支持继续比较目标的上升沿配置，但不是实时电气极性验证。

FB 回调注册移至 probe 初始化成功之后，remove 注销回调、释放 IRQ 后再清理输入 work。stopping 标记在 IRQ 锁下设置，阻止尚未退出的输入 work 在释放 IRQ 后重新 enable_irq。上述为局部生命周期修正，尚未证明 FB/system PM 并发、全局单例或所有移除路径完整可靠。

## 验证

tools/test-f8-touch-transport.py 提取候选中实际的传输与编程序列函数，以主机 GCC、UBSan 和模拟 I²C 调用运行；没有访问硬件。成功路径 306 条写入的寄存器、长度和全部 payload 与独立从原始参考表构造的序列逐字节一致，算法初始化调用两次。

| 注入路径 | 每轮总线事务 | 错误模式 |
| --- | --- | --- |
| 完整编程序列 | 306 | 每个位置分别注入负 errno、短传输 |
| I²C 探测 | 5 | 同上 |
| 内存标志正常 | 2 | 同上 |
| 内存标志不符，探测后重编程 | 313 | 同上 |

共 1252 个故障位置/模式组合，全部验证返回 -EREMOTEIO 或 -EIO，且首次错误后没有任何后续总线事务。UBSan 通过。测试仅覆盖表中提取的传输/序列逻辑，延时、GPIO、真实算法函数和内核并发均为测试替身或不在覆盖范围。

更新后的完整驱动对象另在固定 6.1.172-f8-pro-armbian-eval 环境交叉编译并核对两份内嵌数组。目录内 compile-check.json、transport-check.json 以 candidate_sha256 关联同一版源码；build.log 保存实际构建诊断。没有链接/加载模块或使用新内核运行触摸。

## 待完成

核对原厂复位/启动及算法调用实现，确认 GPIO 供电/时序、控制器状态读回、IRQ 与多触点报告、FB/system PM 并发和触点释放；处理单例及其余资源生命周期。当前保留目标原有寄存器值与延时不代表它们已适配本板。完成后再考虑整合进新的候选内核；当前四件评估产物继续冻结、触摸节点 disabled，原 Arch 恢复系统保留。
