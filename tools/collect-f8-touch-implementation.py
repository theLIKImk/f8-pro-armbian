"""Collect local pinned-source helpers and bounded archived disassembly; offline."""
import json
from pathlib import Path
import subprocess

P = Path('/mnt/d/Netdisk/Other/F8-PRO/archlinux')
source = Path('/var/tmp/f8-pro-armbian/linux-rockchip-config/drivers/input/touchscreen')
out = P / 'analysis/armbian/touch-static'
helpers = out / 'pinned-helpers'
helpers.mkdir(exist_ok=True)
tree = source.parents[2]
for relative in ['arch/arm64/include/asm/delay.h', 'include/asm-generic/delay.h', 'arch/arm64/lib/delay.c']:
    path = tree / relative
    if path.is_file():
        (helpers / relative.replace('/', '-')).write_bytes(path.read_bytes())
files = []
for path in sorted(source.glob('*')):
    if 'gsl' in path.name.lower() or 'tp_suspend' in path.name:
        files.append({'name': path.name, 'bytes': path.stat().st_size, 'is_file': path.is_file()})
        if path.is_file() and (path.name.startswith('tp_suspend') or path.name.startswith('gsl_point')):
            (helpers / path.name).write_bytes(path.read_bytes())
symbols = json.loads((out / 'all-symbols.json').read_text())
starts = sorted(set(item['file_offset'] for item in symbols if item['file_offset'] >= 0))
selected = [item for item in symbols if (21516000 < item['file_offset'] < 21522000 and
            item['type'].lower() == 't') or item['name'] in ['gsl_alg_id_main', 'gsl_DataInit', '__const_udelay']]
records = []
for item in selected:
    start = item['file_offset']
    end = min(offset for offset in starts if offset > start)
    filename = item['name'] + '-' + str(start) + '.asm'
    result = subprocess.check_output(['aarch64-linux-gnu-objdump', '-D', '-b', 'binary', '-m', 'aarch64',
                '--start-address=' + str(start), '--stop-address=' + str(end),
                str(P / 'vendor/ubuntu-5.10.160/boot-assets/Image')], text=True)
    (out / filename).write_text(result)
    records.append({'name': item['name'], 'file_offset': start, 'end_exclusive': end, 'disassembly': filename})
report = {'scope': 'Local source/archive analysis only; no tablet access', 'source_files': files, 'disassembly': records}
(out / 'implementation-index.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
