"""Extract node evidence from the existing dtc-decompiled vendor tree, not a new DT."""
import hashlib
import json
from pathlib import Path
import re

BASE = Path(__file__).resolve().parents[1]
source = BASE / 'analysis/baseline-validation/ubuntu-board.dts'
lines = source.read_text(encoding='utf-8').splitlines()
stack, nodes = [], []
for i, line in enumerate(lines, 1):
    m = re.match(r'\s*([^{};=]+)\s*\{\s*$', line)
    if m:
        name = m[1].strip()
        path = '/' if name == '/' else (stack[-1]['path'].rstrip('/') + '/' + name)
        stack.append({'path': path, 'start_line': i, 'properties': []})
    elif line.strip() == '};':
        node = stack.pop()
        node['end_line'] = i
        nodes.append(node)
    elif stack and line.strip():
        stack[-1]['properties'].append(line.strip())
assert not stack, 'Unbalanced source tree'
selected = []
pattern = re.compile(r'panel@|/backlight$|/ts@|mpu_|ak8963|gc5035|ov8858|es8388|cw2015|charger@|wireless-|/hall|/vibrator')
for n in nodes:
    if pattern.search(n['path']):
        n['vendor_dts'] = '\n'.join(lines[n['start_line']-1:n['end_line']]) + '\n'
        selected.append(n)
phandles = {}
for n in nodes:
    for prop in n['properties']:
        m = re.fullmatch(r'phandle = <(0x[0-9a-f]+)>;', prop)
        if m:
            phandles[m[1]] = n['path']
out = BASE / 'analysis/armbian/board-evidence.json'
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps({'source': str(source.relative_to(BASE)),
    'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
    'scope': 'Vendor node evidence only. Numeric phandles are source-specific; not a compilable port.',
    'nodes': selected, 'phandle_paths': phandles}, indent=2) + '\n', encoding='utf-8')
print(f'Extracted {len(selected)} board nodes and {len(phandles)} phandle references')
