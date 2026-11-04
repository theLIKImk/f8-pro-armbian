"""Serialize heavy disk work; always resume a paused rollback builder."""
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
P=Path(__file__).resolve().parents[1]
def find(script):
    result=[]
    for p in Path('/proc').iterdir():
        if not p.name.isdigit():continue
        try:
            if any(x.endswith(('/'+script).encode()) for x in (p/'cmdline').read_bytes().split(b'\0')):result.append(int(p.name))
        except OSError:pass
    return result
def wait_for(pids):
    while any(Path('/proc',str(pid)).exists() for pid in pids):time.sleep(3)
pack=find('pack-f8-native-desktop-t1.py');rollback=find('build-f8-private-rollback.py')
paused=[]
try:
    for pid in rollback:os.kill(pid,signal.SIGSTOP);paused.append(pid)
    print('Serializing large disk operations: finish native bundle before rollback reconstruction',flush=True)
    wait_for(pack)
    assert (P/'outputs/armbian/official-f8-desktop-t1/native-image-manifest.json').exists(),'Native pack failed; inspect original session'
    if not (P/'outputs/armbian/official-f8-desktop-t1/desktop-bundle.json').exists():
        subprocess.run([sys.executable,str(P/'tools/finalize-f8-desktop-t1.py')],check=True)
finally:
    for pid in paused:
        try:os.kill(pid,signal.SIGCONT)
        except ProcessLookupError:pass
    print('Rollback builder resumed',flush=True)
wait_for(rollback)
assert Path('/var/tmp/f8-pro-armbian/private-backups/20261030-original-root/rollback-manifest.json').exists()
subprocess.run([sys.executable,str(P/'tools/export-f8-private-rollback.py')],check=True)
print('Private ZIP ready for native Windows verification; do not flash until verified',flush=True)
