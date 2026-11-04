#!/bin/sh
# 用 Contents 索引查 org.kde.plasma.battery 归属：
zgrep -l 'plasmoids/org.kde.plasma.battery/metadata.json' /var/lib/apt/lists/ports.ubuntu.com_dists_resolute_Contents-arm64.lz4 2>/dev/null || \
lz4grep 'plasmoids/org.kde.plasma.battery/metadata.json' /var/lib/apt/lists/ports.ubuntu.com_dists_resolute_Contents-arm64.lz4 2>/dev/null | head -3 || \
python3 - <<'PY'
import lz4.frame, glob
# 尝试 lz4 解压查询
try:
    import lz4.frame as lf
    data = lf.open('/var/lib/apt/lists/ports.ubuntu.com_dists_resolute_Contents-arm64.lz4').read().decode('utf-8', 'ignore')
    for line in data.splitlines():
        if 'plasmoids/org.kde.plasma.battery/metadata.json' in line:
            print(line)
except Exception as e:
    print('lz4 err', e)
PY
echo DONE
