set -eu
python3 - <<'PY'
from pathlib import Path
import os,signal,json
expected={78390:('/home/alarm/f8-pro-builds/kwin-6.7.5-v73ibK4G',b'3000'),111334:('/home/alarm/f8-pro-builds/kactivitymanagerd-6.7.5-sZW8PHsH',b'600')}
for pid,(directory,seconds) in expected.items():
    proc=Path('/proc')/str(pid)
    if not proc.exists():
        print('Already finished',pid);continue
    argv=(proc/'cmdline').read_bytes().split(b'\0')[:-1]
    assert argv==[b'timeout',b'--signal=TERM',b'--kill-after=20',seconds,b'makepkg',b'--noconfirm',b'--log'],argv
    assert str((proc/'cwd').resolve())==directory
    assert (proc/'status').read_text().split('Uid:')[1].split()[0]=='1000'
    print('Thermal cooldown: terminate only verified build timeout',pid,directory,flush=True)
    os.kill(pid,signal.SIGTERM)
PY
