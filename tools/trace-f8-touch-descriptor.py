"""Locate static pointers to the bound driver's name in the relocated analysis copy."""
import json
from pathlib import Path
import struct

P = Path(__file__).resolve().parents[1]
OUT = P / 'analysis/armbian/touch-static'
report = json.loads((OUT / 'recovery.json').read_text())
assert report['image_base_anchor_verified'] and report['live_relative_symbols_matched'] == 58
base = report['static_link_base']
data = (OUT / 'relocated-ANALYSIS-ONLY.bin').read_bytes()
symbols = json.loads((OUT / 'all-symbols.json').read_text())
by_offset = {}
for item in symbols:
    by_offset.setdefault(item['file_offset'], []).append(item['name'])
names = []
start = 0
while True:
    start = data.find(b'gslX680_r8\0', start)
    if start < 0:
        break
    pointer = struct.pack('<Q', base + start)
    references, index = [], 0
    while True:
        index = data.find(pointer, index)
        if index < 0:
            break
        relocation_start, relocation_end = report['relocation_table_file_range']
        if index % 8 == 0 and not (relocation_start <= index < relocation_end):
            words = []
            for position in range(max(0, index - 80), min(len(data) - 8, index + 200), 8):
                value = struct.unpack_from('<Q', data, position)[0]
                offset = value - base
                item = {'field_relative_to_name_pointer': position - index, 'image_offset': position}
                if 0 <= offset < len(data):
                    item['pointed_file_offset'] = offset
                    if offset in by_offset:
                        item['symbol_names'] = by_offset[offset]
                    segment = data[offset:offset + 80].split(b'\0', 1)[0]
                    if segment and all(32 <= char <= 126 for char in segment):
                        item['pointed_ascii'] = segment.decode()
                else:
                    item['non_image_pointer_or_value'] = hex(value)
                words.append(item)
            references.append({'name_pointer_file_offset': index, 'nearby_words': words})
        index += 1
    names.append({'driver_name_string_offset': start, 'references': references})
    start += 1
result = {'scope': 'Static pointer neighborhood, struct field identities still need corroboration',
          'bound_driver_name': 'gslX680_r8', 'candidates': names}
(OUT / 'driver-descriptor-candidates.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({'driver': result['bound_driver_name'],
                  'name_string_offsets': [row['driver_name_string_offset'] for row in names],
                  'non_relocation_reference_offsets': [ref['name_pointer_file_offset'] for row in names for ref in row['references']]}, indent=2))
