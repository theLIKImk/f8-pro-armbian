#!/bin/sh
# CW2015 没有绑定在任何总线。原厂 DT 中 CW2015 地址 0x62 通常挂在 I2C6（与 FUSB302 同总线，
# 因为 HANDOFF 记录供电诊断就在 I2C6 读 BQ25890/CW2015）。
# 只读扫描 i2c-6 全地址（不写任何寄存器，i2cdetect 用 SMBus quick 是写操作但无害，
# 不过谨慎起见用 U 布局看现有响应，跳过已绑定地址）：
sudo -n i2cdetect -y -r 6 2>/dev/null || echo scan-blocked
echo "---i2c-0 (PMIC 总线):"
sudo -n i2cdetect -y -r 0 2>/dev/null | head -12
echo DONE
