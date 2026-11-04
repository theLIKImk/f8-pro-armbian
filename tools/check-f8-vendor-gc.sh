#!/bin/sh
# sensor probe 完成后 subdev 应该出现。probe 成功但没 subdev —— 唯一能解释的：
# probe 在 "detected" 之后走了 err 分支（async register 失败会打 dev_err
# "v4l2 async register subdev failed"）—— 但 dmesg 没有这条！
# 或者官方 vendor 的 gc5035 驱动代码与自建树不同（vendor 版 probe 不注册 subdev，
# 而是走 rkaiq 的私有机制）。
# 验证：strings 官方 gc5035.ko 找 subdev 注册相关符号：
strings /lib/modules/6.1.115-vendor-rk35xx/kernel/drivers/media/i2c/gc5035.ko | grep -iE 'v4l2_async|subdev_init|media_entity' | head -6
echo M1
# 若无这些符号 → vendor 驱动是 rkaiq 私有版（不注册 v4l2 subdev）
strings /lib/modules/6.1.115-vendor-rk35xx/kernel/drivers/media/i2c/gc5035.ko | grep -iE 'rkaiq|rkisp|cam' | head -8
echo MARKER_DONE
