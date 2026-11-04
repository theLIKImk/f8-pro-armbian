"""Exact-board factory runtime, isolated and bounded against the C4 kernel."""
import argparse,subprocess
from pathlib import Path
P=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--file',action='store_true');args=parser.parse_args()
s=(P/'local/hardware/camera-c4-aiq-fps14-runner.sh').read_text()
s=s.replace("derived=root/'iqfiles-fps14';assert not derived.exists();derived.mkdir()","derived=root/'iqfiles-fps14';assert derived.is_dir()")
s=s.replace("(derived/name).write_text(json.dumps(changed)+'\\n')","assert json.loads((derived/name).read_text())==changed")
s=s.replace("lib=C.CDLL('/opt/f8-pro-camera/aiq-v6-c4/lib/librkaiq.so')","lib=C.CDLL('/opt/f8-pro-camera/aiq-factory-c4/lib/librkaiq.so')")
s=s.replace('back-aiq-fps14.log','back-aiq-factory-fps14.log').replace('back-aiq-fps14-640x480.nv12','back-aiq-factory-fps14-640x480.nv12')
anchor="root=Path('/opt/f8-pro-camera/aiq-v6-c4');folder=Path('/run/f8-camera-c4')\n"
install='''import hashlib
library=Path('/opt/f8-pro-camera/aiq-factory-c4/lib/librkaiq.so');assert not library.exists()
data=Path('/home/f8test/.cache/f8-camera-aiq-c4-stage/librkaiq-factory.so').read_bytes()
assert hashlib.sha256(data).hexdigest()=='9454a6627a4de88dbf065843ed183bb14c737cd4ccc136dd86d5a64d55722af9'
library.parent.mkdir(parents=True,exist_ok=True);library.write_bytes(data);library.chmod(0o644)
p=subprocess.run(['ldd',str(library)],capture_output=True,text=True,timeout=8)
assert p.returncode==0 and 'not found' not in p.stdout+p.stderr,(p.stdout,p.stderr)
'''
assert s.count(anchor)==1;s=s.replace(anchor,anchor+install)
suffix='factory-aiq-file' if args.file else 'factory-aiq'
if args.file:
    s=s.replace('assert not library.exists()','assert library.exists()')
    s=s.replace('library.parent.mkdir(parents=True,exist_ok=True);library.write_bytes(data);library.chmod(0o644)','assert library.read_bytes()==data')
    s=s.replace("b'/opt/f8-pro-camera/aiq-v6-c4/iqfiles-fps14'","b'/opt/f8-pro-camera/aiq-v6-c4/iqfiles-fps14/ov8858_HS5885-BNSM1018-V01_default.json'")
    s=s.replace('back-aiq-factory-fps14.log','back-aiq-factory-file-fps14.log').replace('back-aiq-factory-fps14-640x480.nv12','back-aiq-factory-file-fps14-640x480.nv12')
r=P/f'local/hardware/camera-c4-{suffix}-runner.sh';assert not r.exists();r.write_text(s)
p=subprocess.run(['python3',str(P/'tools/ssh-f8-desktop.py'),'--address','192.168.1.227','--script',str(r),'--sudo'],capture_output=True,text=True,timeout=90)
assert p.returncode==0,p.stderr
(P/f'local/hardware/camera-c4-{suffix}-test01.json').write_text(p.stdout)
print('Saved exact-board factory runtime comparison')
