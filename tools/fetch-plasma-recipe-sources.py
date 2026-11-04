"""Verify release sources corresponding to the collected recipe candidate graph."""
import json
from pathlib import Path
import subprocess
import sys

root = Path(__file__).resolve().parent.parent
graph = json.loads((root/'analysis/plasma-6.7.5/recipe-dependencies.json').read_text())
assert not graph['errors'] and graph['version'] == '6.7.5'
source_names={'polkit-kde-agent':'polkit-kde-agent-1'}
packages = sorted(source_names.get(name,name) for name in graph['recipes'])
raise SystemExit(subprocess.run([sys.executable, str(root/'tools/fetch-plasma-sources.py'),
                                 '--packages', *packages]).returncode)
