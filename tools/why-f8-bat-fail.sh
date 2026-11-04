#!/bin/sh
# 电池已恢复（cw2015-battery 回来了，服务 active）。
# 排查它开机为何没绑成：看服务首次运行的 journal
sudo -n journalctl -u f8-battery-cw2015 -b --no-pager -q | head -10
echo "---"
systemctl show f8-battery-cw2015 -p ExecMainStatus -p Result -p ExecMainExitTimestamp
echo DONE
