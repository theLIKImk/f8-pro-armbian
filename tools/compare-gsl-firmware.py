"""Compare upstream static GSL tables against the archived, uncompressed vendor Image.

An exact full-table match is positive byte evidence. A miss alone cannot identify
the vendor table or prove driver incompatibility (layout/optimization may differ).
"""
import hashlib
import json
from pathlib import Path
import re
import struct

BASE = Path(__file__).resolve().parents[1]
image = (BASE / 'vendor/ubuntu-5.10.160/boot-assets/Image').read_bytes()
root = BASE / 'analysis/armbian/source-audit/linux-rockchip/drivers/input/touchscreen'
results = []
for name in ['gsl3673.h', 'gslx680_pad.h']:
    source = (root / name).read_text()
    source = re.sub(r'/\*.*?\*/|//[^\n]*', '', source, flags=re.S)
    for m in re.finditer(r'(?:static\s+)?(?:const\s+)?struct\s+fw_data\s+(\w+)\s*\[\s*\]\s*=\s*\{(.*?)\n\};', source, re.S):
        pairs = re.findall(r'\{\s*(0x[0-9a-fA-F]+|\d+)\s*,\s*(0x[0-9a-fA-F]+|\d+)\s*\}', m[2])
        assert pairs, m[1]
        blob = b''.join(struct.pack('<II', int(a, 0), int(b, 0)) for a, b in pairs)
        index = image.find(blob)
        results.append({'header': name, 'table': m[1], 'entries': len(pairs),
                        'bytes': len(blob), 'table_sha256': hashlib.sha256(blob).hexdigest(),
                        'vendor_image_offset': index if index >= 0 else None,
                        'exact_full_match': index >= 0})
    for m in re.finditer(r'(?:unsigned int|unsigned|u32|int)\s+(\w*config_data\w*)\s*\[\s*\]\s*=\s*\{(.*?)\};', source, re.S):
        values = re.findall(r'0x[0-9a-fA-F]+|\b\d+\b', m[2])
        if not values:
            continue
        blob = b''.join(struct.pack('<I', int(v, 0)) for v in values)
        index = image.find(blob)
        results.append({'header': name, 'table': m[1], 'kind': 'algorithm_config',
                        'entries': len(values), 'bytes': len(blob),
                        'table_sha256': hashlib.sha256(blob).hexdigest(),
                        'vendor_image_offset': index if index >= 0 else None,
                        'exact_full_match': index >= 0})
assert results, 'No firmware arrays parsed'
result = {'vendor_image_sha256': hashlib.sha256(image).hexdigest(),
          'layout_assumption': 'little-endian 8-byte fw_data: 32-bit storage for offset bitfield + 32-bit value',
          'scope': 'Static comparison only, no device access or firmware upload.', 'tables': results}
out = BASE / 'analysis/armbian/gsl-firmware-comparison.json'
out.write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
