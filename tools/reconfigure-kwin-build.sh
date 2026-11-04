set -eu
python3 - <<'PY'
from pathlib import Path
import os,signal
expected='/home/alarm/f8-pro-builds/kwin-6.7.5-v73ibK4G'
found=[]
for p in Path('/proc').iterdir():
    if not p.name.isdecimal():continue
    try:
        args=(p/'cmdline').read_bytes().split(b'\0')[:-1]
        if len(args)>1 and args[0]==b'python3' and args[1]==b'native-build-supervisor.py' and str((p/'cwd').resolve())==expected:
            assert (p/'status').read_text().split('Uid:')[1].split()[0]=='1000'
            found.append(int(p.name))
    except (FileNotFoundError,PermissionError,ProcessLookupError):pass
assert len(found)==1,found
os.kill(found[0],signal.SIGTERM)
print('Stopped only verified KWin build supervisor for controlled jobs change',found[0])
PY
