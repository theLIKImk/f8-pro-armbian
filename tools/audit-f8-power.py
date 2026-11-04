"""Compare archived F8-PRO regulator constraints with the pinned single-RK806 DTS."""
import hashlib
import json
from pathlib import Path
import re

BASE = Path(__file__).resolve().parents[1]
OUT = BASE / 'analysis/armbian'
vendor = BASE / 'analysis/baseline-validation/ubuntu-board.dts'
candidate = OUT / 'source-audit/linux-rockchip/arch/arm64/boot/dts/rockchip/rk3588-rk806-single.dtsi'


def nodes(path):
    stack, result = [], {}
    for line in path.read_text().splitlines():
        m = re.match(r'\s*([^{};=]+)\s*\{\s*$', line)
        if m:
            name = m[1].strip().split(':')[-1].strip()
            parent = stack[-1]['path'] if stack else ''
            stack.append({'name': name, 'path': parent + '/' + name, 'props': {}})
        elif line.strip() == '};':
            n = stack.pop()
            result[n['path']] = n
        elif stack:
            m = re.match(r'\s*([\w,#-]+)(?:\s*=\s*(.*?))?;\s*$', line)
            if m:
                val = m[2] or True
                if isinstance(val, str) and re.fullmatch(r'<[\dxXa-fA-F\s]+>', val):
                    val = [int(x, 0) for x in val[1:-1].split()]
                stack[-1]['props'][m[1]] = val
    assert not stack
    return result


old, new = nodes(vendor), nodes(candidate)
old_rails = {n['name']: n for n in old.values() if '/rk806single@0/regulators/' in n['path'] and n['name'].startswith(('DCDC_REG', 'PLDO_REG', 'NLDO_REG'))}
new_rails = {n['name']: n for n in new.values() if n['name'] in old_rails}
report = []
for name, n in old_rails.items():
    other = new_rails.get(name)
    assert other, name
    def tree_props(items, rail):
        props = {}
        for path, item in items.items():
            if path == rail['path'] or path.startswith(rail['path'] + '/'):
                rel = path[len(rail['path']):] or '/'
                for key, val in item['props'].items():
                    if key != 'phandle':
                        props[rel + ':' + key] = val
        return props
    a, b = tree_props(old, n), tree_props(new, other)
    differences = [{'property': key, 'vendor': a.get(key), 'candidate': b.get(key)}
                   for key in sorted(a.keys() | b.keys()) if a.get(key) != b.get(key)]
    report.append({'rail': name, 'vendor_name': n['props'].get('regulator-name'), 'differences': differences})
result = {'scope': 'Static DTS constraints only; no register read or device writes.',
          'vendor_dts_sha256': hashlib.sha256(vendor.read_bytes()).hexdigest(),
          'candidate_dtsi_sha256': hashlib.sha256(candidate.read_bytes()).hexdigest(),
          'rails': report}
(OUT / 'power-rail-comparison.json').write_text(json.dumps(result, indent=2) + '\n')
for r in report:
    print(r['rail'], r['vendor_name'], json.dumps(r['differences']))
