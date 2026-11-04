#!/bin/sh
# ISP pad0 的三个 rawrd 链接全部无状态标记（[]）—— RAW 路径未选通。
# 这是 rkisp 的设计：SDITF→ISP 通过 RAW 读取通道。检查 rawrd 节点属于哪个 media：
# media2 里 rkisp_rawrd0_m 无 ENABLED —— 意味着 sditf→rkisp 的链在 DT 里
# 有了（endpoint 存在）但 media 链接未 enable。
# rkisp 需要先在 media 图上 enable 正确的 rawrd 链接。
# 检查 rawrd 实体与 sditf 的连接：
sudo -n media-ctl -d /dev/media2 -p 2>/dev/null | grep -B3 -A6 'rawrd'
echo "---"
sudo -n media-ctl -d /dev/media3 -p 2>/dev/null | grep -B3 -A6 'rawrd' | head -20
echo DONE
