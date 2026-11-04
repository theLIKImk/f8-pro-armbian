#!/bin/sh
# 真相：服务在 01:54:03（内核时间约173秒）确实绑定了！Instantiated 出现了。
# 但用户开机时没图标 —— 因为这次开机（885620bb）是 U5 回退后第一次启动，
# 服务跑了、也成功了（01:54:03 = 当前 boot）。用户说"没图标"是在此之前？
# 时间轴：01:51:17 模块加载 → 01:54:03 绑定成功 → 用户看屏幕没图标。
# 可能 WirePlumber/UPower 在绑定发生前已经枚举过，之后没刷新（upower 需要重新触发）。
# 但 01:54:03 就绑定了，图标应该后来会出现。用户报告时间点更晚……
# 无论如何现在设备在、UPower 认。验证 upower + KDE：
export XDG_RUNTIME_DIR=/run/user/1601
upower -e 2>/dev/null | grep battery
echo "---"
sudo -n systemctl restart upower
sleep 3
upower -e 2>/dev/null | grep battery
echo DONE
