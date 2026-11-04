"""Record actual ARM64 C-array serialization checks against archived selected bytes."""
import hashlib
import json
from pathlib import Path
import struct
import subprocess

P = Path(__file__).resolve().parents[1]
work = Path('/var/tmp/f8-pro-armbian/touch-reference')
profile = P / 'armbian/touch/reference-r8-shuping'
header = (work / 'profile.o').read_bytes()[:64]
assert header[:6] == b'\x7fELF\x02\x01' and struct.unpack_from('<H', header, 18)[0] == 183
checks = []
for name in ['firmware', 'algorithm']:
    original, serialized = (profile / (name + '-reference.bin')).read_bytes(), (work / (name + '.bin')).read_bytes()
    assert original == serialized
    checks.append({'name': name, 'bytes': len(serialized), 'sha256': hashlib.sha256(serialized).hexdigest()})
report = {'scope': 'Cross-compiled array layout/content only; not a touch driver build, upload or runtime test',
          'compiler': subprocess.check_output(['aarch64-linux-gnu-gcc', '--version'], text=True).splitlines()[0],
          'architecture': 'AArch64', 'target_fw_data_struct_size': 8,
          'checks': checks, 'new_kernel_touch_enabled': False}
(P / 'analysis/armbian/touch-static/reference-compile-check.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
