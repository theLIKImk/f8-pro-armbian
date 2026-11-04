import json,subprocess
from pathlib import Path
P=Path(__file__).resolve().parents[1];dest=P/'local/hardware/armbian-native-usb-20261101'
runner=dest/'full-pstore-runner.sh';out=dest/'u1-full-pstore01.json';assert not out.exists()
runner.write_text("#!/bin/sh\nset -eu\npython3 -I - <<'PY'\nimport json\nfrom pathlib import Path\nprint(json.dumps({p.name:p.read_text(errors='replace') for p in Path('/sys/fs/pstore').glob('*') if p.is_file()}))\nPY\n")
r=subprocess.run(['python3',str(P/'tools/ssh-f8-desktop.py'),'--address','192.168.1.227','--script',str(runner),'--sudo'],capture_output=True,text=True,timeout=100)
assert r.returncode==0,r.stderr[-1300:]
d=json.loads(r.stdout);out.write_text(json.dumps(d,indent=2)+'\n')
for name,text in d.items():
    lines=text.splitlines();print(name,'bytes',len(text));print('\n'.join(lines[:30]));print('\n'.join(s for s in lines if any(k in s for k in ['Machine model','Kernel command line','INIT STOP','f8_usb','f8-otg','usb-otg','panic','Oops'])))
