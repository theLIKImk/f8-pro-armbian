"""Validate archived r8 IRQ request arguments without accessing the tablet."""
import json
from pathlib import Path
import struct

P = Path(__file__).resolve().parents[1]
out = P / 'analysis/armbian/touch-static'
dispatch = json.loads((out / 'firmware-dispatch.json').read_text())
assert dispatch['probe_offset'] == 21520308
image = (P / 'vendor/ubuntu-5.10.160/boot-assets/Image').read_bytes()
symbols = json.loads((out / 'all-symbols.json').read_text())
def instruction(offset):
    return struct.unpack_from('<I', image, offset)[0]
assert instruction(0x14864e4) == 0xd2800023  # mov x3, #1: flags
assert instruction(0x14864ec) == 0xd2800002  # mov x2, #0: thread_fn
call = instruction(0x14864f0)
assert call & 0xfc000000 == 0x94000000
immediate = call & 0x3ffffff
if immediate & (1 << 25):
    immediate -= 1 << 26
target = 0x14864f0 + immediate * 4
assert any(item['file_offset'] == target and item['name'] == 'request_threaded_irq' for item in symbols)
report = {'scope': 'Archived r8 probe static IRQ request arguments only; no electrical/live IRQ verification',
          'driver': dispatch['driver_name'], 'probe_offset': dispatch['probe_offset'],
          'request_call_offset': 0x14864f0, 'request_symbol': 'request_threaded_irq',
          'flags_argument': 1, 'thread_fn_is_null': True,
          'of_gpio_flags_are_irq_trigger_flags': False,
          'runtime_polarity_verified': False}
(out / 'irq-request.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
