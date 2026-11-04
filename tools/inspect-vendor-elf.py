"""Static inspection only: never execute recovered Ubuntu programs."""
import hashlib
import json
from pathlib import Path
import re
import subprocess

project = Path(__file__).resolve().parent.parent
source = project / 'analysis/vendor-userspace'
records = json.loads((source / 'manifest.json').read_text())
report = []
for record in records:
    path = source / record['file']
    assert hashlib.sha256(path.read_bytes()).hexdigest() == record['sha256']
    if not path.read_bytes().startswith(b'\x7fELF'):
        continue
    header = subprocess.run(['readelf', '-h', str(path)], capture_output=True, text=True, check=True).stdout
    dynamic = subprocess.run(['readelf', '-d', str(path)], capture_output=True, text=True, check=True).stdout
    program = subprocess.run(['readelf', '-l', str(path)], capture_output=True, text=True, check=True).stdout
    report.append({**record, 'machine': re.search(r'Machine:\s*(.+)', header).group(1),
                   'needed': re.findall(r'\(NEEDED\).*?\[(.*?)\]', dynamic),
                   'interpreter': re.findall(r'Requesting program interpreter:\s*(.*?)\]', program),
                   'executed': False})
(source / 'elf-dependencies.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
