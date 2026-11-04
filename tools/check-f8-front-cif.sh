#!/bin/sh
# 后摄 video22 也黑（Y=11）—— 因为 RKAIQ worker 没跑（预览已关），ISP 无 3A 时全黑。
# 这证实：**此平台 ISP 无 3A 就不出正常图**，路线 A"固定曝光直出"对 ISP 路径不成立。
# 前摄唯一绕过 ISP 的路：CIF 直出 RG10（C4 曾成功 2 帧 2592x1944）→ 软件 debayer。
# 验证 CIF 直出对前摄当前是否仍可用（C4 时是 video? 的 CIF 节点）：
sudo -n dmesg | grep -iE 'front|cif.*raw|RG10' | grep -vE 'apparmor|audit' | tail -5
echo M1
# CIF stream 节点现状：
grep -H . /sys/class/video4linux/*/name | grep -E 'stream_cif_mipi_id0' | head -4
echo MARKER_DONE
