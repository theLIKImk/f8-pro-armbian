"""Build missing host modpost from the exact official header sources.

Avoid modules_prepare: this header package omits unrelated arch preparation inputs.
Target type offsets are generated with the ARM64 compiler and official headers.
"""
import json
from pathlib import Path
import re
import shutil
import subprocess

PROJECT = Path('/mnt/d/Netdisk/Other/F8-PRO/archlinux')
BASE = Path('/var/tmp/f8-pro-armbian')
H = BASE / 'official-kernel/usr/src/linux-headers-6.1.115-vendor-rk35xx'
W = BASE / 'official-host-tools'
W.mkdir(exist_ok=True)
# Restore packaged generated/configuration files after the failed modules_prepare.
records = json.loads((PROJECT / 'analysis/armbian/repository/downloaded-kernel-packages.json').read_text())
record = next(r for r in records if r['package'].startswith('linux-headers'))
subprocess.run(['dpkg-deb', '--extract', str(PROJECT / record['file'].replace('\\', '/')),
                str(BASE / 'official-kernel')], check=True)


def run(args):
    subprocess.run([str(x) for x in args], check=True, cwd=H)


run(['gcc', '-O2', H / 'scripts/basic/fixdep.c', '-o', H / 'scripts/basic/fixdep'])
run(['gcc', '-O2', H / 'scripts/mod/mk_elfconfig.c', '-o', W / 'mk_elfconfig'])
run(['aarch64-linux-gnu-gcc', '-c', H / 'scripts/mod/empty.c', '-o', W / 'empty.o'])
with (W / 'empty.o').open('rb') as source, (W / 'elfconfig.h').open('wb') as target:
    subprocess.run([str(W / 'mk_elfconfig')], stdin=source, stdout=target, check=True)
includes = ['arch/arm64/include', 'arch/arm64/include/generated', 'include',
            'arch/arm64/include/uapi', 'arch/arm64/include/generated/uapi',
            'include/uapi', 'include/generated/uapi']
flags = [value for name in includes for value in ['-I', str(H / name)]]
run(['aarch64-linux-gnu-gcc', '-S', '-D__KERNEL__', '-mgeneral-regs-only', '-fno-pie',
     *flags, '-include', H / 'include/linux/kconfig.h',
     H / 'scripts/mod/devicetable-offsets.c', '-o', W / 'devicetable-offsets.s'])
text = (W / 'devicetable-offsets.s').read_text()
offsets = re.findall(r'->([A-Za-z_]\w*)\s+[#$]?(-?\d+)\s', text)
assert len(offsets) > 100, 'Expected target device-table offsets'
(W / 'devicetable-offsets.h').write_text('#ifndef __DEVICETABLE_OFFSETS_H__\n#define __DEVICETABLE_OFFSETS_H__\n' +
    ''.join(f'#define {key} {value}\n' for key, value in offsets) + '#endif\n')
run(['gcc', '-O2', '-I', W, '-I', H / 'scripts/mod',
     H / 'scripts/mod/modpost.c', H / 'scripts/mod/file2alias.c', H / 'scripts/mod/sumversion.c',
     '-o', H / 'scripts/mod/modpost'])
print(f'Official-source fixdep/modpost ready; {len(offsets)} target offsets generated')
