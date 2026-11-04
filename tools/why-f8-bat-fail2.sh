#!/bin/sh
# 服务开机显示 Finished/成功，但设备当时没创建 —— 因为/modules-load 在服务之后？
# modules-load systemd-modules-load.service 是 systemd-tmpfiles-setup 之前跑的，
# 服务 After=multi-user.target 应该够晚。但 01:54:03 服务跑时模块 01:51:17 已加载。
# 那为何 new_device 没生效？可能服务跑时 echo 'cw2015 0x62' 里 0x62 被解释对了，
# 但 cw2015 驱动 probe 失败一次（如 FUSB 占线时序），设备没创建但 sh 返回 0。
# dmesg 时间轴查证：
sudo -n dmesg | grep -iE 'cw2015' | head -6
echo "---"
# 关键：看看 boot_id 885620bb 这次启动里 new_device 有没有出现：
sudo -n journalctl -k -b --no-pager -q | grep -i 'new_device' | head -3
echo DONE
