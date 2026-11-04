"""Extract a reference profile selected by the archived bound driver, never enable it."""
import hashlib
import json
from pathlib import Path
import re
import struct

P = Path(__file__).resolve().parents[1]
OUT = P / 'analysis/armbian/touch-static'
report = json.loads((OUT / 'firmware-dispatch.json').read_text())
selected = report['selected_by_observed_compatible']
live = json.loads((P / 'analysis/armbian/touch-input-metadata.json').read_text())
assert live['compatible'] == [selected['compatible']]
assert list(live['devices'][0]['axes'][key]['maximum'] for key in ['ABS_MT_POSITION_X', 'ABS_MT_POSITION_Y']) == selected['config_words_at_24_28']
original = (P / 'vendor/ubuntu-5.10.160/boot-assets/Image').read_bytes()
relocated = (OUT / 'relocated-ANALYSIS-ONLY.bin').read_bytes()
profile = P / 'armbian/touch/reference-r8-shuping'
profile.mkdir(parents=True, exist_ok=True)
firmware = original[selected['firmware_offset']:selected['firmware_offset'] + selected['firmware_bytes']]
algorithm = original[selected['algorithm_offset']:selected['algorithm_offset'] + selected['algorithm_bytes']]
assert firmware == relocated[selected['firmware_offset']:selected['firmware_offset'] + selected['firmware_bytes']]
assert algorithm == relocated[selected['algorithm_offset']:selected['algorithm_offset'] + selected['algorithm_bytes']]
assert hashlib.sha256(firmware).hexdigest() == selected['firmware_sha256']
assert hashlib.sha256(algorithm).hexdigest() == selected['algorithm_sha256']
assert struct.unpack_from('<I', algorithm, 4)[0] == 512
(profile / 'firmware-reference.bin').write_bytes(firmware)
(profile / 'algorithm-reference.bin').write_bytes(algorithm)
pairs = list(struct.iter_unpack('<II', firmware))
words = list(struct.unpack('<512I', algorithm))
header = ('/* Archived F8-PRO r8/shuping reference only; NOT enabled or hardware-tested on 6.1. */\n'
          '#ifndef F8_PRO_R8_SHUPING_REFERENCE_H\n#define F8_PRO_R8_SHUPING_REFERENCE_H\n'
          'static const struct fw_data f8_pro_r8_shuping_fw[] = {\n')
header += ''.join(f'    {{0x{offset:02x}, 0x{value:08x}}},\n' for offset, value in pairs)
header += '};\nstatic unsigned int f8_pro_r8_shuping_algorithm[] = {\n'
header += ''.join('    ' + ', '.join(f'0x{value:08x}' for value in words[index:index + 8]) + ',\n'
                  for index in range(0, len(words), 8))
header += '};\n#endif\n'
(profile / 'f8-pro-r8-shuping-reference.h').write_text(header)
# Compile with the target driver's actual struct declaration, not an invented layout.
source = (P / 'analysis/armbian/source-audit/linux-rockchip/drivers/input/touchscreen/gsl3673.h').read_text()
declaration = re.search(r'struct fw_data\s*\{.*?\};', source, re.S)[0]
unit = ('typedef unsigned int u32;\n' + declaration + '\n'
        '#include "f8-pro-r8-shuping-reference.h"\n'
        '_Static_assert(sizeof(struct fw_data) == 8, "fw_data ABI");\n'
        '_Static_assert(sizeof(f8_pro_r8_shuping_fw) == 38808, "firmware length");\n'
        '_Static_assert(sizeof(f8_pro_r8_shuping_algorithm) == 2048, "algorithm length");\n')
(profile / 'compile-reference.c').write_text(unit)
metadata = {'scope': 'Archived selected profile/reference C header only; not a driver integration or runtime proof',
            'source_image_sha256': hashlib.sha256(original).hexdigest(), 'firmware': selected,
            'observed_abs_mt_max': selected['config_words_at_24_28'],
            'original_bytes_equal_relocated_analysis': True, 'new_kernel_profile_enabled': False,
            'algorithm_runtime_contents_verified': False,
            'c_header_sha256': hashlib.sha256(header.encode()).hexdigest()}
(profile / 'provenance.json').write_text(json.dumps(metadata, indent=2) + '\n')
print(json.dumps({'firmware_bytes': len(firmware), 'algorithm_bytes': len(algorithm), 'reference_header_generated': True}))
