"""Verify the isolated kernel object retains the exact selected profile arrays."""
import hashlib
import json
from pathlib import Path
import subprocess

P = Path('/mnt/d/Netdisk/Other/F8-PRO/archlinux')
out = P / 'armbian/touch/candidate-r8-shuping'
work = Path('/var/tmp/f8-pro-armbian/touch-driver-candidate')
preparation = json.loads((out / 'preparation.json').read_text())
source = Path('/var/tmp/f8-pro-armbian/linux-rockchip-config/drivers/input/touchscreen/gsl3673.c').read_text()
assert hashlib.sha256(source.encode()).hexdigest() == preparation['source_sha256_normalized']
obj = work / 'gsl3673.o'
assert hashlib.sha256((work / 'gsl3673.c').read_bytes()).hexdigest() == preparation['candidate_sha256']
elf = subprocess.check_output(['aarch64-linux-gnu-readelf', '-h', str(obj)], text=True)
assert 'AArch64' in elf and 'REL (Relocatable file)' in elf
nm = subprocess.check_output(['aarch64-linux-gnu-nm', '-S', '--defined-only', str(obj)], text=True)
symbols = {}
for line in nm.splitlines():
    fields = line.split()
    if len(fields) == 4:
        offset, size, section, name = fields
        symbols[name] = (int(offset, 16), int(size, 16), section)
subprocess.run(['aarch64-linux-gnu-objcopy', '--dump-section', f'.rodata={work}/rodata.bin',
                '--dump-section', f'.data={work}/data.bin', str(obj), str(work / 'section-copy.o')], check=True)
checks = []
for name, kind, section, filename in [
        ('f8_pro_r8_shuping_fw', 'r', 'rodata.bin', 'firmware-reference.bin'),
        ('f8_pro_r8_shuping_algorithm', 'd', 'data.bin', 'algorithm-reference.bin')]:
    offset, size, actual_kind = symbols[name]
    assert actual_kind.lower() == kind
    compiled = (work / section).read_bytes()[offset:offset + size]
    reference = (P / 'armbian/touch/reference-r8-shuping' / filename).read_bytes()
    assert compiled == reference
    checks.append({'symbol': name, 'bytes': size, 'sha256': hashlib.sha256(compiled).hexdigest()})
report = {'scope': 'Isolated kernel driver object compilation and embedded-array verification; no module link/load or runtime test',
          'kernel_release': (Path('/var/tmp/f8-pro-armbian/kernel-config-build/include/config/kernel.release')).read_text().strip(),
          'source_matches_pinned_tree': True, 'elf_machine': 'AArch64',
          'object_sha256': hashlib.sha256(obj.read_bytes()).hexdigest(),
          'candidate_sha256': preparation['candidate_sha256'],
          'arrays': checks, 'new_kernel_touch_enabled': False,
          'algorithm_irq_reset_pm_runtime_verified': False}
(out / 'compile-check.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
