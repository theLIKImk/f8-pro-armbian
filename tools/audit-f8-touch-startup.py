"""Check archived r8 startup call and busy-loop constants, without runtime reads."""
import hashlib
import json
from pathlib import Path
import struct

P = Path(__file__).resolve().parents[1]
out = P / 'analysis/armbian/touch-static'
image = (P / 'vendor/ubuntu-5.10.160/boot-assets/Image').read_bytes()
symbols = json.loads((out / 'all-symbols.json').read_text())
def word(offset):
    return struct.unpack_from('<I', image, offset)[0]
def call_target(offset):
    value = word(offset)
    assert value & 0xfc000000 == 0x94000000
    immediate = value & 0x3ffffff
    if immediate & (1 << 25):
        immediate -= 1 << 26
    return offset + immediate * 4
assert word(0x1485448) == 0xf940a2a0  # private data -> board config +320
assert word(0x148544c) == 0xf9400800  # config -> algorithm +16
algorithm = call_target(0x1485450)
assert any(item['name'] == 'gsl_DataInit' and item['file_offset'] == algorithm for item in symbols)
# Three reset-loop counters: decrement before delay, hence 21 -> 20 iterations.
for offset, instruction in [(0x14852fc, 0xd28002b4), (0x1485370, 0xd2800174),
                             (0x14853a0, 0xd2800173), (0x1485418, 0xd2800174)]:
    assert word(offset) == instruction
for offset, instruction in [(0x1485304, 0xd2912b15), (0x1485308, 0xf2a00835),
                             (0x148535c, 0xd2912b15), (0x1485374, 0xf2a00835),
                             (0x1485394, 0xd2912b14), (0x148539c, 0xf2a00834),
                             (0x1485420, 0xd2912b16), (0x1485424, 0xf2a00836),
                             (0x1485344, 0xf1000694), (0x1485380, 0xf1000694),
                             (0x14853b4, 0xf1000673), (0x1485468, 0xf1000694)]:
    assert word(offset) == instruction
delay = call_target(0x1485350)
assert any(item['name'] == '__const_udelay' and item['file_offset'] == delay for item in symbols)
for offset in [0x148538c, 0x14853c0, 0x1485474]:
    assert call_target(offset) == delay
header = (out / 'pinned-helpers/include-asm-generic-delay.h').read_text()
assert '__const_udelay((n) * 0x10c7ul)' in header
assert 0x418958 == 1000 * 0x10c7
report = {'scope': 'Archived r8 static call/loop analysis, with nominal delay inferred using pinned generic delay macro',
          'image_sha256': hashlib.sha256(image).hexdigest(),
          'startup_algorithm_symbol': 'gsl_DataInit', 'startup_algorithm_offset': algorithm,
          'algorithm_pointer_from_selected_board_config': True,
          'reset_delay_loop_iterations': [20,10,10], 'startup_delay_loop_iterations': 10,
          'inferred_nominal_reset_ms': [20,10,10], 'inferred_nominal_startup_ms': 10,
          'real_elapsed_time_verified': False, 'algorithm_binary_identity_verified': False}
(out / 'startup-contract.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
