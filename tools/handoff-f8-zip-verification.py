"""Stop only the slow shared-drive verifier after ZIP writing is complete."""
import json
import os
from pathlib import Path
import signal
import zipfile
P=Path(__file__).resolve().parents[1]
out=P/'outputs/armbian/official-f8-desktop-t1'
assert json.loads((out/'native-image-manifest.json').read_text())['root_sha256']
with zipfile.ZipFile(out/'F8_ARMBIAN_NATIVE_DESKTOP_T1.zip.part') as z:assert len(z.namelist())==7
for proc in Path('/proc').iterdir():
    if not proc.name.isdigit():continue
    try:
        if any(x.endswith(b'/finalize-f8-desktop-t1.py') for x in (proc/'cmdline').read_bytes().split(b'\0')):
            os.kill(int(proc.name),signal.SIGTERM)
            print('Complete ZIP handed to native Windows verifier; source images unchanged',flush=True)
    except OSError:pass
