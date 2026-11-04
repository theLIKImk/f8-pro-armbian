"""Disassemble only selected archived functions using corroborated file offsets."""
import json
from pathlib import Path
import subprocess

P = Path(__file__).resolve().parents[1]
OUT = P / 'analysis/armbian/touch-static'
all_symbols = json.loads((OUT / 'all-symbols.json').read_text())
starts = sorted(set(item['file_offset'] for item in all_symbols if item['file_offset'] >= 0))
selected = [item for item in all_symbols if item['name'] in ['gsl_load_fw', 'gsl_ts_probe', 'gsl_ts_init']]
records = []
for symbol in selected:
    start = symbol['file_offset']
    end = min(offset for offset in starts if offset > start)
    name = symbol['name'] + '-' + str(start) + '.asm'
    command = ['wsl', '-d', 'rg35xx-build', '-u', 'root', '--', 'aarch64-linux-gnu-objdump',
               '-D', '-b', 'binary', '-m', 'aarch64', '--start-address=' + str(start), '--stop-address=' + str(end),
               '/mnt/d/Netdisk/Other/F8-PRO/archlinux/vendor/ubuntu-5.10.160/boot-assets/Image']
    result = subprocess.run(command, capture_output=True, text=True, encoding='utf-8', timeout=100)
    assert result.returncode == 0, result.stderr[-300:]
    (OUT / name).write_text(result.stdout, encoding='utf-8')
    records.append({'name': symbol['name'], 'file_offset': start, 'end_exclusive': end, 'disassembly': name})
(OUT / 'disassembly-index.json').write_text(json.dumps(records, indent=2) + '\n')
print(json.dumps(records, indent=2))
