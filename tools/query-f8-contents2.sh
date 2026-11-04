#!/bin/sh
python3 - <<'PY'
import lz4.frame as lf
for f in ['/var/lib/apt/lists/ports.ubuntu.com_dists_resolute_Contents-arm64.lz4',
          '/var/lib/apt/lists/ports.ubuntu.com_dists_resolute-updates_Contents-arm64.gz',
          '/var/lib/apt/lists/ports.ubuntu.com_dists_resolute-security_Contents-arm64.gz']:
    try:
        if f.endswith('.lz4'):
            data = lf.open(f).read().decode('utf-8','ignore')
        else:
            import gzip
            data = gzip.open(f).read().decode('utf-8','ignore')
        for line in data.splitlines():
            if 'org.kde.plasma.battery' in line and 'plasma/battery' not in line:
                print(f.split('_dists_')[1], '|', line[:120])
    except Exception as e:
        print(f, 'err', e)
PY
echo DONE
