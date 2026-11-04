import json, hashlib, os, time

# C3 决策记录：采用 initramfs early modprobe 还是内核重编？
# 评估：
# 1. 内编（=y）：需重编 vmlinux + Image（约30-60分钟，12核7G内存偏紧），但效果最确定——
#    sensor probe 发生在内核启动早期（device_initcall），必然早于 rkcif/dphy notifier。
#    风险：内核映像哈希全变，FIT 需重建（已有成熟流程）。
# 2. initramfs early modprobe：改 ramdisk 加 gc5035/ov8858.ko + 早于 sd driver probe 的
#    modprobe 调用。rkcif 是内建还是模块？若 rkcif 内建，其 notifier 在内核 init 时完成，
#    ramdisk 里的 modprobe 仍晚于它 —— 无效！
# 关键判定：查当前 Image 里 rkcif 是否内建。

print('需要确认 rkcif/dphy 是否内建，才能定方案。')
