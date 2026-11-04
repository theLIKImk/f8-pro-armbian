"""Corroborate bound-driver descriptor -> OF match data -> archived firmware table."""
import hashlib
import json
from pathlib import Path
import struct

P = Path(__file__).resolve().parents[1]
OUT = P / 'analysis/armbian/touch-static'
recovery = json.loads((OUT / 'recovery.json').read_text())
base = recovery['static_link_base']
data = (OUT / 'relocated-ANALYSIS-ONLY.bin').read_bytes()


def pointer(offset):
    value = struct.unpack_from('<Q', data, offset)[0] - base
    assert 0 <= value < len(data), offset
    return value


def cstring(offset, limit=128):
    return data[offset:offset + limit].split(b'\0', 1)[0].decode('ascii')


# The archived gsl_ts_init at 28786068 passes ADRP(0x24a7000)+0x250
# to i2c_register_driver. Verify the actual instruction words, not just names.
assert struct.unpack_from('<I', data, 28786084)[0] == 0x900049a1
assert struct.unpack_from('<I', data, 28786092)[0] == 0x91094021
call_instruction = struct.unpack_from('<I', data, 28786100)[0]
assert call_instruction & 0xfc000000 == 0x94000000
immediate = call_instruction & 0x3ffffff
if immediate & (1 << 25):
    immediate -= 1 << 26
call_target = 28786100 + immediate * 4
symbols = json.loads((OUT / 'all-symbols.json').read_text())
assert any(item['file_offset'] == call_target and item['name'] == 'i2c_register_driver' for item in symbols)
driver = 0x24a7250
name = pointer(driver + 56)
assert cstring(name) == 'gslX680_r8'
probe = pointer(driver + 8)
assert probe == 21520308
of_table = pointer(driver + 96)
matches = []
for index in range(8):
    entry = of_table + index * 200
    compatible = cstring(entry + 64)
    if not compatible:
        break
    assert data[entry:entry + 64] == bytes(64), 'Unexpected OF name/type matching constraints'
    datum = pointer(entry + 192)
    firmware = pointer(datum)
    entries = struct.unpack_from('<I', data, datum + 8)[0]
    assert 0 < entries < 100000 and firmware + entries * 8 <= len(data)
    blob = data[firmware:firmware + entries * 8]
    assert all(struct.unpack_from('<I', blob, position)[0] <= 0xff for position in range(0, len(blob), 8))
    algorithm = pointer(datum + 16)
    config_words = struct.unpack_from('<I', data, algorithm + 4)[0]
    assert config_words == 512 and algorithm + config_words * 4 <= len(data)
    config = data[algorithm:algorithm + config_words * 4]
    screen_words = list(struct.unpack_from('<II', data, datum + 24))
    matches.append({'compatible': compatible, 'of_entry_offset': entry, 'match_data_offset': datum,
                    'firmware_offset': firmware, 'firmware_entries': entries, 'firmware_bytes': len(blob),
                    'firmware_sha256': hashlib.sha256(blob).hexdigest(),
                    'algorithm_offset': algorithm, 'algorithm_declared_u32_words': config_words, 'algorithm_bytes': len(config),
                    'algorithm_sha256': hashlib.sha256(config).hexdigest(), 'config_words_at_24_28': screen_words})
selected = next(item for item in matches if item['compatible'] == 'gslX680_shuping')
comparison = json.loads((P / 'analysis/armbian/gsl-firmware-comparison.json').read_text())
fw = next(row for row in comparison['tables'] if row['table'] == 'GSL3673_FW')
algorithm = next(row for row in comparison['tables'] if row['table'] == 'gsl_config_data_id_3673')
report = {'scope': 'Static archived dispatch path corroborated by live binding; no firmware sent or new driver tested',
          'driver_descriptor_offset': driver, 'driver_name': 'gslX680_r8', 'probe_offset': probe,
          'registration_call_target_verified': 'i2c_register_driver',
          'of_table_offset': of_table, 'matches': matches,
          'selected_by_observed_compatible': selected,
          'selected_firmware_matches_target_GSL3673_FW': selected['firmware_sha256'] == fw['table_sha256'],
          'selected_algorithm_matches_target_3673': selected['algorithm_sha256'] == algorithm['table_sha256'],
          'algorithm_length_field_verified': True, 'algorithm_runtime_contents_verified': False,
          'new_kernel_touch_enabled': False}
(OUT / 'firmware-dispatch.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
