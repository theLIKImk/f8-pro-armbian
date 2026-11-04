> **2026-11-01 最新状态入口：[C3失败后回退C2进度](RESUME-CAMERA-AFTER-C3-20261101.md)。C2已启动且双sensor绑定，但仍无法取帧；C3因误用6.1.172内核构建失败，禁止刷入，已回退C2。旧“C2待刷”及“C3待刷”均作废。probe时序为待证假设，禁止热重绑。本轮仅核对文档并更新记录，未操作硬件。

# C3 构建失败复盘与相机链路完整交接（2026-11-01）

> 本文档给下一个接手相机适配的 AI。C2 能启动、双 sensor 绑定成功，但取帧失败。
> C3 尝试用"sensor 驱动内编"解决 probe 时序，但构建用了错误源码树，已失败回退。

## 一、C3 失败复盘（构建者错误）

**错误经过**：C3 计划把 gc5035/ov8858 从模块改为内编（=y），解决"rkcif notifier 在 sensor probe 前完成"的时序问题。构建时使用了 `kernel-config-build` 树（6.1.172 自建评估树，commit 85233a85b），但 **C1/C2 实际运行的是 Armbian 官方 vendor 6.1.115-rk35xx Image**（`build@armbian` 编译），两者不同源。

**证据**：
- C2 kernel：46,561,792 字节，`Linux version 6.1.115-vendor-rk35xx (build@armbian)`，含 rkcif(501处)/rkisp(939处) 字符串
- C3 kernel：34,300,416 字节，6.1.172 自建，rkcif/rkisp/bcmdhd/panthor 全部为 0
- 结果：无法启动（用户刷入后无显示，已回退 C2）

**教训**：
1. 改内核配置必须 diff 确认只有目标行变化（`olddefconfig` 有副作用时必须逐项核对）
2. 分清两条构建线：**vendor Image（官方二进制+DTB）** vs **自建树（kernel-config-build，6.1.172，仅用于模块编译如 cw2015）**。vendor 驱动适配需重编 vendor 内核时，必须先取 6.1.115 对应源码（blob:none 部分克隆里没有历史）

## 二、相机链路调查结论（截至 C2）

### 2.1 已确认正常
- DT 图完整且与原厂 board.dtb 一致（逐段 remote-endpoint 双向核对，tools/f8-phresolve.py）
- sditf 交叉（前→rkisp1、后→rkisp0）是原厂设计，非错误
- 双 sensor 芯片识别成功（C2 修复了 MCLK pinctrl 冲突）

### 2.2 核心异常（未解决）
- rkcif 的 22 个 video 节点 open() 返回 **ENODEV**（sysfs 存在、81:0 主次号存在，但 cdev 打不开）
- rkisp 系 video22-39 全部正常
- `rkcif_update_sensor_info: get remote terminal sensor failed -19` 持续循环
- v4l2-async pending 列表：**全链互等**（sensor、dphy×2、mipi-csi2×2、rkcif×2、rkisp×2 全部挂起）
- `clear unready subdev num: 1`（rkcif 在 2.6s 主动放弃等待）

### 2.3 已排除/已试无效
- DT 端点缺失：证伪（见 2.1）
- sensor probe 失败：证伪（芯片 ID 读出）
- `echo 1 > /sys/module/video_rkcif/parameters/clr_unready_dev`：官方恢复机制，触发后无效果
- 热重绑 CIF/DPHY：禁止（C1 触发 rkcif_do_soft_reset NULL Oops）

### 2.4 关键源码线索（6.1.172 树，路径与行号）
- `drivers/media/platform/rockchip/cif/dev.c`
  - L2342 `cif_subdev_notifier()`：rkcif notifier 用 `v4l2_async_nf_parse_fwnode_endpoints` 遍历**自己节点的端点**，asd fwnode = remote endpoint（即 mipi-csi2 侧端点）
  - L3487 `clr_unready_dev` module_param；L3496 `late_initcall(rkcif_clr_unready_dev)`（内建时 init 末尾调用一次）
  - L2371 `notifier_isp_thread`：wait_for_completion_timeout 5s 后 `subdev_asyn_register_itf`
  - L2170 `subdev_asyn_register_itf`：CONFIG_NO_GKI=y 下先 `rkcif_update_sensor_info`，失败则打印 "There is not terminal subdev" 并 return（不注册 sditf）
- `drivers/media/v4l2-core/v4l2-async.c` L95-140：fwnode 异构匹配（endpoint vs device 取 port parent 比较）——理论支持 endpoint→device 匹配
- `drivers/media/v4l2-core/v4l2-fwnode.c` L1286 `v4l2_async_register_subdev_sensor`：只解析 flash-leds/lens-focus，主 subdev 用 dev fwnode（i2c 节点）注册

### 2.5 未验证的关键疑点（下一个 AI 优先查）

**(a) C1 与 C2 行为差异（最可能突破口）**
- C1：22 个 rkcif video 节点**注册成功**（当时只有 GC5035 一颗 sensor 识别成功，OV8858 因 pin 冲突失败）
- C2：双 sensor 都成功，rkcif video 反而 ENODEV
- C1→C2 仅改：MCLK pinctrl 从 sensor 移到电源 regulator、VCM disable
- **行动**：`diff` `/var/tmp/f8-pro-armbian/camera-c1/fdt` 与 `camera-c2/fdt`（先 dtc 反编译），逐属性找出全部差异；怀疑方向是 C2 删除 sensor pinctrl-0 后，某个依赖关系（fw_devlink supplier）变化导致 rkcif probe 顺序/结果不同

**(b) v4l2-async 匹配未发生的机理**
- pending 列表互等说明 fwnode 匹配未发生
- 需读 **6.1.115 vendor 内核**实际的 v4l2-async.c（不是 6.1.172！），确认 Rockchip 是否有私有补丁改变匹配行为
- 6.1.115 源码获取：Armbian 官方 github（linux-rockchip 仓库对应 26.8.1 发布的 commit），或尝试 `git fetch origin` 更新部分克隆

**(c) sensor 驱动版本差异**
- vendor gc5035.ko/ov8858.ko（设备 /lib/modules/…/media/i2c/，vermagic 6.1.115）确认调用 `v4l2_async_register_subdev_sensor`，与自建树 6.1.172 一致——此项已排除

### 2.6 建议行动顺序

1. **diff C1/C2 fdt**（dtc 反编译后逐属性对比）——寻找 rkcif video 注册失败的诱因
2. 若确认 pinctrl 改动是诱因：构建 **C3-1** = 官方 vendor Image + 恢复 sensor pinctrl-0 的 DTB + VCM 保持 disabled（不需要重编内核！C1/C2 流程已验证 boot 打包链路）
3. 若 diff 无发现：获取 6.1.115 源码，读 vendor v4l2-async.c 的匹配实现
4. 也可并行实验：在 C2 上用 fw_devlink 手动解除/重建 supplier 关系（`/sys/class/devices/.../supplier:*`）观察 async 行为

## 三、构建资产现状

| 资产 | 位置 | 说明 |
| --- | --- | --- |
| 官方 vendor 内核包 | `/var/tmp/f8-pro-armbian/official-kernel/` | Image+modules+headers+config（CIF/RKISP=y），boot/config/dtb/System.map/vmlinuz 齐 |
| 自建树（6.1.172） | `/var/tmp/f8-pro-armbian/kernel-config-build/` | 仅用于树外模块编译（cw2015/bq25890 已验证）；**勿再用于 vendor Image 构建** |
| camera-c1/c2/c3 构建树 | `/var/tmp/f8-pro-armbian/camera-c{1,2,3}/` | fdt/kernel/ramdisk/resource/boot.its |
| C2 镜像（可用） | `outputs/armbian/official-f8-camera-c2/BOOT_ONLY_ARMBIAN_CAMERA_C2.img` | SHA `41b1f3f8…8bb7247f`，当前设备运行中 |
| S1 回退基线 | `outputs/armbian/official-f8-motion-s1/BOOT_ONLY_ARMBIAN_MOTION_S1.img` | SHA `1b39e4e0…5dd682c7` |
| C3 镜像（勿刷） | `outputs/armbian/official-f8-camera-c3/BOOT_ONLY_ARMBIAN_CAMERA_C3.img` | 错误源码产物，留档 |

## 四、设备当前状态（2026-11-01 回退后）

- boot `6b50d20b-56e6-48b9-834e-b8ebb3260b31`，SSH 192.0.2.227 f8test，running
- C2 系统：双 sensor 绑定（gc5035 5-0037、ov8858 5-0036），44 个 video 节点
- 已禁操作：CIF/DPHY 热重绑（C1 Oops）；其它硬件 root 配置/校准保持
