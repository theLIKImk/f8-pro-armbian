"""Apply tested ADC refresh to RAM only, rolling back on setup/validation failure."""
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
out=P/'local/hardware/armbian-official-g6-r5-20261030-01'
resultfile=out/'sampling-refresh-fix-01.json';runner=out/'sampling-refresh-fix-runner.sh'
assert not resultfile.exists() and not runner.exists()
fixture=json.loads((P/'analysis/armbian/live-g6/power-refresh-fixtures.json').read_text());assert fixture['passed']
base=P/'outputs/armbian/official-f8-live-g6-r5';meta=json.loads((base/'preflight.json').read_text())
blob=(base/meta['candidate_file']).read_bytes();assert hashlib.sha256(blob).hexdigest()==meta['candidate_sha256']
props=fdt(blob)['/images/ramdisk'];start=int.from_bytes(props['data-position'],'big');size=int.from_bytes(props['data-size'],'big')
spec=importlib.util.spec_from_file_location('cpio',P/'tools/build-usb-bootlog.py')
helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
records={n:b for n,v,b in helper.cpio_read(gzip.decompress(blob[start:start+size]))}
expected=hashlib.sha256(records['f8-g3-assets/live-power.sh']).hexdigest()
files={name:(P/path).read_bytes() for name,path in {
 'live-power.sh':'armbian/official-graphics/live-power.sh',
 'power-refresh.py':'armbian/official-graphics/power-refresh.py',
 'bq-adc-oneshot.py':'armbian/power/bq-adc-oneshot.py'}.items()}
encoded={name:base64.b64encode(body).decode() for name,body in files.items()}
code='''import base64,hashlib,json,subprocess,time
from pathlib import Path
assert any(line.split()[1:3]==['/','overlay'] for line in Path('/proc/mounts').read_text().splitlines())
directory=Path('/usr/libexec/f8-pro');names=PAYLOAD
assert hashlib.sha256((directory/'live-power.sh').read_bytes()).hexdigest()==EXPECTED
backup=Path('/run/f8/power-refresh-before-01');backup.mkdir()
previous={}
for name in names:
    path=directory/name
    previous[name]=path.read_bytes() if path.exists() else None
    if previous[name] is not None:(backup/name).write_bytes(previous[name])
def service(action):subprocess.run(['systemctl',action,'f8-live-power.service'],check=True,timeout=8)
service('stop')
try:
    for name,encoded in names.items():
        data=base64.b64decode(encoded)
        if name.endswith('.py'):compile(data,name,'exec')
        target=directory/name;tmp=target.with_suffix('.refresh-new')
        with tmp.open('xb') as stream:stream.write(data)
        tmp.chmod(0o755 if name.endswith('.sh') else 0o644);tmp.replace(target)
    service('start')
    deadline=time.monotonic()+20;observations=[]
    while True:
        current=json.loads(Path('/run/f8/power-current.json').read_text())
        if 'adc_refresh' in current and current['monotonic_seconds']>deadline-20:break
        if time.monotonic()>deadline:raise RuntimeError('New sampler did not publish')
        time.sleep(0.5)
    for index in range(3):
        current=json.loads(Path('/run/f8/power-current.json').read_text())
        assert current['complete'] and 'adc_refresh' in current
        assert time.monotonic()-current['monotonic_seconds']<25
        observations.append({'snapshot_seconds':current['monotonic_seconds'],'adc_refresh':current['adc_refresh'],
           'bq':current['devices']['0x6a']['decoded'],'cw':current['devices']['0x62']['decoded']})
        if index<2:time.sleep(11)
    active=subprocess.check_output(['systemctl','is-active','f8-live-power.service'],text=True).strip()
    assert active=='active'
except Exception:
    service('stop')
    for name,data in previous.items():
        target=directory/name
        if data is None:target.unlink(missing_ok=True)
        else:
            target.write_bytes(data);target.chmod(0o755 if name.endswith('.sh') else 0o644)
    service('start')
    raise
print(json.dumps({'scope':'RAM-only input-powered ADC refresh fix, no charge policy writes',
 'backup':str(backup),'service':active,'observations':observations,
 'files':{name:hashlib.sha256((directory/name).read_bytes()).hexdigest() for name in names},
 'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip()},indent=2))
'''.replace('PAYLOAD',repr(encoded)).replace('EXPECTED',repr(expected))
runner.write_text("set -eu\ntest \"$(uname -r)\" = 6.1.115-vendor-rk35xx\npython3 -I - <<'F8_REFRESH_FIX'\n"+code+'\nF8_REFRESH_FIX\n')
r=subprocess.run(['python3',str(P/'tools/ssh-f8-live.py'),'--address','192.168.1.227','--script',str(runner),'--sudo'],capture_output=True,text=True,timeout=80)
assert r.returncode==0,r.stderr[-2200:]
data=json.loads(r.stdout)
with resultfile.open('x') as stream:stream.write(json.dumps(data,indent=2)+'\n')
print(json.dumps(data,indent=2))
