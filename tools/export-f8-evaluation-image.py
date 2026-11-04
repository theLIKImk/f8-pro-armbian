"""Export a completed custom Image, labelling its core-only symbol table correctly."""
import hashlib
import json
from pathlib import Path
import shutil
import struct
import subprocess

P = Path(__file__).resolve().parents[1]
B = Path('/var/tmp/f8-pro-armbian/kernel-config-build')
S = Path('/var/tmp/f8-pro-armbian/linux-rockchip-config')
expected = '85233a85b67928000afc2e966bab86a8c414f1b4'
assert subprocess.check_output(['git', '-C', str(S), 'rev-parse', 'HEAD'], text=True).strip() == expected
release = (B / 'include/config/kernel.release').read_text().strip()
assert release == '6.1.172-f8-pro-armbian-eval', release
image = B / 'arch/arm64/boot/Image'
content = image.read_bytes()
assert content[56:60] == b'ARM\x64', 'Not an ARM64 Linux Image'
# This is _end - _text, including runtime BSS, rather than just file bytes.
runtime_size = struct.unpack_from('<Q', content, 16)[0]
assert runtime_size >= len(content) and runtime_size > 0, 'Image runtime size mismatch'
log = (B / 'evaluation-image.log').read_text(errors='replace')
assert 'arch/arm64/boot/Image' in log and not any(
    line.startswith('make') and '***' in line for line in log.splitlines()), 'Check build log'
assert (B / 'vmlinux.symvers').stat().st_size > 0
out = P / 'outputs/armbian/evaluation-kernel'
report_dir = P / 'analysis/armbian/kernel-build'
out.mkdir(parents=True, exist_ok=True)
report_dir.mkdir(parents=True, exist_ok=True)
files = []
for name, source in [('Image', image), ('vmlinux.symvers', B / 'vmlinux.symvers'),
                     ('System.map', B / 'System.map'), ('evaluation.config', B / '.config')]:
    destination = out / name
    shutil.copy2(source, destination)
    with destination.open('rb') as stream:
        digest = hashlib.file_digest(stream, 'sha256').hexdigest()
    files.append({'name': name, 'bytes': destination.stat().st_size, 'sha256': digest})
report = {'scope': 'Custom base-source Image only; no full framework patches, matching modules or board boot validation',
          'commit': expected, 'release': release, 'architecture': 'ARM64',
          'runtime_image_bytes': runtime_size,
          'symbol_table_scope': 'vmlinux core exports only; not full Module.symvers',
          'files': files}
(report_dir / 'verified-evaluation-image.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
