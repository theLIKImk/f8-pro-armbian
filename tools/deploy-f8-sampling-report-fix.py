"""Update only diagnostic report semantics in RAM; no charger configuration writes."""
import base64
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'tools'))
from inspect_images import fdt
spec=importlib.util.spec_from_file_location('cpio',P/'tools/build-usb-bootlog.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
oldmeta=json.loads((P/'outputs/armbian/official-f8-power-g5/preflight.json').read_text())
blob=(P/'outputs/armbian/official-f8-power-g5'/oldmeta['candidate_file']).read_bytes()
assert hashlib.sha256(blob).hexdigest()==oldmeta['candidate_sha256']
props=fdt(blob)['/images/ramdisk'];a=int.from_bytes(props['data-position'],'big');n=int.from_bytes(props['data-size'],'big')
records={name:body for name,values,body in m.cpio_read(gzip.decompress(blob[a:a+n]))}
old=records['f8-g3-assets/power-readonly.py'];expected=hashlib.sha256(old).hexdigest()
new=(P/'armbian/official-graphics/power-readonly.py').read_bytes()
compile(new,'power-readonly.py','exec')
out=P/'local/hardware/armbian-official-g6-r5-20261030-01'
script=out/'sampling-report-fix-runner.sh';resultfile=out/'sampling-report-fix-01.json'
assert not script.exists() and not resultfile.exists()
code='''import base64,hashlib,json,os,subprocess
from pathlib import Path
p=Path('/usr/libexec/f8-pro/power-readonly.py')
old=p.read_bytes()
assert hashlib.sha256(old).hexdigest()==EXPECTED
new=base64.b64decode(PAYLOAD)
compile(new,str(p),'exec')
backup=Path('/run/f8/power-readonly-before-report-fix.py')
with backup.open('xb') as stream:stream.write(old)
temp=p.with_name('power-readonly.report-fix.tmp')
with temp.open('xb') as stream:stream.write(new)
temp.chmod(0o644);temp.replace(p)
test=Path('/run/f8/power-report-audit-validation-01.json')
assert not test.exists()
r=subprocess.run(['python3','-I',str(p),'--output',str(test)],capture_output=True,text=True,timeout=15)
assert r.returncode==0,r.stderr
data=json.loads(test.read_text());bq=data['devices']['0x6a']['decoded']
assert bq['battery_current_channel_validated'] is False and bq['silicon_manufacturer_verified'] is False
print(json.dumps({'scope':'RAM-only diagnostic report semantics fix, no charging policy writes',
 'old_sha256':hashlib.sha256(old).hexdigest(),'new_sha256':hashlib.sha256(new).hexdigest(),
 'backup':str(backup),'probe_complete':data['complete'],'decoded_bq':bq,
 'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip()},indent=2))
'''.replace('EXPECTED',repr(expected)).replace('PAYLOAD',repr(base64.b64encode(new).decode()))
script.write_text("set -eu\ntest \"$(uname -r)\" = 6.1.115-vendor-rk35xx\npython3 -I - <<'F8_FIX_PY'\n"+code+'\nF8_FIX_PY\n')
r=subprocess.run(['python3',str(P/'tools/ssh-f8-live.py'),'--address','192.168.1.227','--script',str(script),'--sudo'],capture_output=True,text=True,timeout=60)
assert r.returncode==0,r.stderr[-1600:]
data=json.loads(r.stdout)
with resultfile.open('x') as stream:stream.write(json.dumps(data,indent=2)+'\n')
print(json.dumps(data,indent=2))
