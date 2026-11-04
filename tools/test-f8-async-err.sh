#!/bin/sh
# async grep 没输出（可能 journal 权限）。看 sensor 驱动注册失败的直接证据：
# 官方 gc5035 probe 末尾会打印注册错误（若有）。检查完整 probe 日志：
sudo -n dmesg | grep -A3 'detected gc5035' | tail -8
echo "=== 对照：ov8858 ==="
sudo -n dmesg | grep -A3 'Detected OV008858' | tail -8
echo "=== 关键测试：sensor subdev 注册需要 i2c 设备的 of_node 完整 port/endpoint ——"
echo "    而这已在 DT 里。驱动 probe 末尾若 async 注册失败会打 v4l2_err。搜 v4l2 错误:"
sudo -n dmesg | grep -iE 'v4l2.*(err|fail)|async.*(fail|err)' | tail -6
echo MARKER_DONE
