> **2026-11-01 最新状态入口：[C3失败后回退C2进度](RESUME-CAMERA-AFTER-C3-20261101.md)。C2已启动且双sensor绑定，但仍无法取帧；C3因误用6.1.172内核构建失败，禁止刷入，已回退C2。旧“C2待刷”及“C3待刷”均作废。probe时序为待证假设，禁止热重绑。本轮仅核对文档并更新记录，未操作硬件。

# C2 冷启动取帧验证结果（2026-11-01）

## 重要更正（同日深度核对后）

初版本文判断“mipi-csi2↔CIF 断链”**有误**：实机解析脚本键前缀错误（// vs /）导致假阴性。用本地构建树 FDT 与原厂 board.dtb 对照后确认：

- **C2 的 DT 图与原厂完全一致，无缺失**：sensor↔dphy↔mipi-csi2↔rkcif 全部双向 remote-endpoint 正确
- sditf 交叉（前→rkisp1、后→rkisp0）**就是原厂设计**，不是错误
- 无需 C3 补端点

## 真正的根因：probe 时序

- 实机三现象：rkcif video ENODEV、sensor subdev 不进 media 图、rkcif_update_sensor_info failed -19 循环
- 时间线：CIF async notifier 在 2.6s completed（当时 sensor 尚未 probe）；gc5035/ov8858 作为模块在 7.2s 才被 f8-camera-start.service 触发 probe
- v4l2_async 行为：notifier 完成后，后注册的 subdev 不会与之重新绑定（部分场景支持，但 rkcif 的 notifier 匹配表是静态的）
- 原厂之所以能工作：原厂内核 sensor 驱动是**内建**（=y），probe 在 CIF 之前自然完成

## 修复方向（C3）

把 gc5035/ov8858 驱动内编进内核（CONFIG_*_TIMER=y）或在 initramfs 中 early modprobe，使 sensor probe 早于 rkcif/dphy 的 notifier 完成。热重绑/重 probe 方案不可行（C1 已验证触发 rkcif_do_soft_reset Oops）。

## C2 冷启动实测记录（保留）

## 环境确认

- 用户已刷 C2，boot `ea2df972-9e85-49d7-8646-ec6703e73cca`，SSH 192.0.2.227 正常
- `f8-camera-start.service` active，冷启动流程执行完成（initial probe，无 unbind）
- 双 sensor 绑定：`gc5035 5-0037`（前）、`ov8858 5-0036`（后），芯片实测读出：
  - `gc5035 5-0037: detected gc5035 sensor`（driver 00.01.05）
  - `ov8858 5-0036: Detected OV008858 sensor, REVISION 0xb2`（driver 00.01.06）
- 共享 MCLK 冲突（C1 的失败点）**已解决**

## 取帧验证过程

1. **ISP mainpath 直取**（video22/video31，NV12 800x600）：
   - 首次 STREAMON → `Operation not permitted`，内核 `check rkisp_mainpath link or isp input`
   - 用 `media-ctl -l '"rkisp_rawrd0_m":0->"rkisp-isp-subdev":0[1]'` 接通 RAW 读链（可逆配置）后重试 → **select timeout**（sensor 未出流）
2. **CIF 直出路径**：所有 rkcif video 节点（video0–21）open 返回 **ENODEV**
   - 分类探测：可开的只有 rkisp 系（video22–39），rkcif 系全部失败
   - sysfs 有名字但内核未注册 video_device

## 根因定位（重要更正：初版断链判断作废）

初版曾判断“mipi-csi2↔CIF 断链”——**实机解析脚本键前缀错误（// vs /）导致假阴性**。后用本地构建树 FDT（与实机同源）+ 原厂 board.dtb dtc 反编译逐段对照确认：

| 链路段 | C2 vs 原厂 |
| --- | --- |
| gc5035 ↔ dphy1 | ✅ 双向正确 |
| dphy1 ↔ mipi2-csi2 | ✅ 双向正确 |
| mipi2-csi2 ↔ rkcif-mipi-lvds2 | ✅ 双向正确 |
| ov8858 ↔ dphy2 ↔ mipi3-csi2 ↔ lvds3 | ✅ 双向正确 |
| sditf2(前) → rkisp1-vir0 | ✅ 与原厂一致（原厂就是前→ISP1） |
| sditf3(后) → rkisp0-vir0 | ✅ 与原厂一致 |

**C2 的 DT 图无缺失，无需 C3 补端点。**

## 附带确认

- dmesg 时序：dphy/csi2/CIF 在 2.6s probe 完成，sensor 在 7.2s probe；CIF notifier 在 sensor 之前"completed"（clear unready subdev num: 1），之后 sensor probe 成功但已无人等待
- pstore/ramoops 无 6.1 内核记录；journal 内核日志完整
- 本轮未触热重绑禁令；media-ctl enable 为可逆配置

## 下一步（C3 方向：改 probe 时序，不改 DT）

1. **推荐**：C3 把 gc5035/ov8858 驱动内编进内核（CONFIG_VIDEO_GC5035=y / CONFIG_VIDEO_OV8858=y）或在 initramfs 中 early modprobe，让 sensor probe 早于 rkcif/dphy 的 notifier 完成
2. 热重绑/重 probe 方案不可行（C1 已验证触发 rkcif_do_soft_reset Oops）
3. C3 若重编 kernel，需同步 FIT；仅改模块加载方式则只动 initramfs/BOOT ramdisk
4. 回退基线 S1 不变

## 本轮涉及文件

- `tools/f8-phresolve.py` — 运行 FDT 解析（phandle/endpoint/remote 全量）
- `tools/test-f8-c2-frame*.sh`、`check-f8-*.sh` — 取帧与诊断脚本
- HANDOFF.md 顶部已记录本轮结论
