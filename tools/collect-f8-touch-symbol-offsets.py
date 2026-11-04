"""Read symbol metadata via SSH, saving reference-relative offsets rather than runtime addresses."""
import json
from pathlib import Path
import struct
import subprocess

P = Path(__file__).resolve().parents[1]
command = ['wsl', '-d', 'rg35xx-build', '-u', 'root', '--', 'ssh',
           '-i', '/var/tmp/f8-pro-archlinux-20261027/private-keys/f8-pro-test-ed25519',
           '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=8', '-o', 'IdentitiesOnly=yes',
           '-o', 'StrictHostKeyChecking=yes', '-o', 'UserKnownHostsFile=/var/tmp/f8-pro-archlinux-20261027/test-known-hosts',
           'alarm@192.168.1.227',
           "uname -r; readlink /sys/bus/i2c/devices/4-0040/driver; sudo -n grep -iE ' (_text|_stext|_end|.*gsl.*|report_data)$' /proc/kallsyms"]
result = subprocess.run(command, capture_output=True, text=True, encoding='utf-8', timeout=100)
assert result.returncode == 0, 'Read-only symbol query failed: ' + result.stderr[-300:]
lines = result.stdout.splitlines()
release, driver = lines[:2]
symbols = []
for line in lines[2:]:
    fields = line.split()
    if len(fields) >= 3:
        symbols.append((int(fields[0], 16), fields[1], fields[2]))
reference = '_text' if any(name == '_text' for _, _, name in symbols) else '_stext'
base = next(address for address, _, name in symbols if name == reference)
assert base != 0, 'Symbols are masked; no sysctl changes permitted'
image = P / 'vendor/ubuntu-5.10.160/boot-assets/Image'
with image.open('rb') as stream:
    header = stream.read(64)
runtime_size = struct.unpack_from('<Q', header, 16)[0]
assert release == '5.10.160'
end = next((address for address, _, name in symbols if name == '_end'), None)
span_verified = None
if reference == '_text' and end is not None:
    assert end - base == runtime_size
    span_verified = True
entries = [{'name': name, 'type': kind, 'reference_relative_offset': address - base}
           for address, kind, name in symbols if name not in ['_text', '_stext', '_end']]
report = {'scope': 'Read-only kallsyms metadata only; no kernel/process memory read, no firmware upload',
          'kernel_release': release, 'bound_driver': driver.rsplit('/', 1)[-1],
          'reference_symbol': reference, 'image_base_proven': reference == '_text' and span_verified is True,
          'runtime_span_matches_archived_image_header': span_verified, 'archived_runtime_span_bytes': runtime_size,
          'runtime_addresses_saved': False, 'symbols': entries}
(P / 'analysis/armbian/touch-symbol-offsets.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
