#!/bin/sh
dpkg -L powerdevil | head -30
echo "=== powerdevil-data ==="
dpkg -L powerdevil-data | head -20
echo "=== 装的 powerdevil 版本 vs Contents 索引版本 ==="
dpkg -l powerdevil | tail -1
echo DONE
