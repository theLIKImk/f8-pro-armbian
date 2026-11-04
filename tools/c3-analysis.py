import json

# 关键结论汇总：
# 1. 官方 vendor Image：rkcif/rkisp/dphy 全部内建（modinfo 找不到模块），只有 sensor 是模块。
# 2. rkcif 内建 → notifier 在内核 init 完成（2.6s）→ sensor 模块 7.2s 才加载 → 断链。
# 3. 修复必须让 sensor probe 早于 notifier：
#    - 方案A：sensor 模块放进 initramfs 并在 initramfs 的 init 里 modprobe。
#      但 rkcif 内建在 kernel init 时已 notifier complete —— initramfs 阶段
#      内核还没启动完？错：initramfs 的 /init 执行时 kernel init 尚未结束？
#      不：initramfs 在 kernel init 完成后由 kernel 执行 /init，此时 rkcif
#      driver 已 probe（device_initcall）→ notifier 已完成 → 无效。
#    - 方案B：sensor 模块改为 initcall 早期加载？模块只能在用户态加载。
#    - 方案C：用 CONFIGmoduleId= 修改 rkcif？不可行。
#    - 方案D：**把 sensor 驱动源码放进官方 6.1.115 vendor 源码树重编为内建**
#      —— 但我们没有 6.1.115 源码树（只有 6.1.172 的部分克隆）。
#      Armbian 官方 vendor 内核源码：github.com/armbian/linux-rockchip tag
#      对应 26.8.1 发布 = rk-6.1-rkr5？需要确认 6.1.115 对应的 tag/commit。
#    - 方案E：**修改 rkcif 驱动的 notifier 行为**（打补丁支持 late binding）——
#      C1 的 Oops 说明热 unbind/bind 崩溃，但 late sensor attach 若走正常
#      v4l2_async_register_subdev 路径应安全（sensor probe 后注册 subdev，
#      v4l2_async 会尝试匹配 pending notifier —— 但 rkcif notifier 已 complete）。
#      v4l2_async 框架其实支持：notifier complete 后新 subdev 注册会立即尝试匹配
#      已完成 notifier 的 waiting 列表？不：complete 后 waiting 列表已清空。
#    - 方案F：重新审视 —— rkcif 的 notifier 用 fwnode 匹配 sensor endpoint。
#      sensor 模块加载后 v4l2_async_register_subdev 会查找现有 notifier。
#      rkcif notifier complete 表示它已放弃等待。但如果我们把 rkcif 的
#      notifier 改为不 complete（等待），sensor 后到就能匹配 —— 这是上游
#      v4l2-async 的标准行为（notifier 会一直等待所有匹配项）。
#      问题可能是 rkcif notifier 的匹配表里 sensor endpoint 不在 —— 因为
#      rkcif 用 v4l2_async_nf_add_fwnode_remote 只加了一层（mipi-csi2），
#      靠子设备级联注册。mipi-csi2 也是内建先注册，它的 notifier 又等 dphy，
#      dphy 等 sensor。级联中 complete 逐层向上 —— sensor 迟到时整条链都不匹配。
#      v4l2-async 理论上支持迟到 subdev 匹配（async_register 会扫描所有
#      notifier 的 asd 列表）—— 除非 rkcif/mipi-csi2 的 notifier 已经 complete
#      并释放。确实：complete 后 notifier 从 waiting 列表移除，迟到者无法匹配。
# 4. 可行最小修复：**让 sensor 模块在 rkcif probe 之前加载** —— 模块内建在
#    rootfs 的 /lib/modules 但通过 **内核命令行无参数能做**；但 systemd-modules-load
#    太晚。**udev 触发太晚**。唯一内核级方案 = 内编。
# 5. 所以回到方案D：获取 6.1.115 源码。Armbian 官方仓库分支/tag 需要查询。
print("结论：需要 6.1.115 vendor 源码树。查 Armbian 官方发布对应 commit。")
