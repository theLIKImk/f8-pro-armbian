"""Verify r6 cold-boot payloads and several sampler cycles over authenticated SSH."""
import datetime
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'tools'))
from inspect_images import fdt
base=P/'outputs/armbian/official-f8-live-g6-r6';meta=json.loads((base/'preflight.json').read_text())
image=(base/meta['candidate_file']).read_bytes();assert hashlib.sha256(image).hexdigest()==meta['candidate_sha256']
prop=fdt(image)['/images/ramdisk'];a=int.from_bytes(prop['data-position'],'big');size=int.from_bytes(prop['data-size'],'big')
spec=importlib.util.spec_from_file_location('cpio',P/'tools/build-usb-bootlog.py')
helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
assets={n:b for n,v,b in helper.cpio_read(gzip.decompress(image[a:a+size]))}
names=['live-power.sh','power-refresh.py','bq-adc-oneshot.py','power-readonly.py','graphics-run']
expected={n:hashlib.sha256(assets['f8-g3-assets/'+n]).hexdigest() for n in names}
out=P/'local/hardware/armbian-official-g6-r6-20261030-01';out.mkdir(exist_ok=True)
resultfile=out/'boot-verification.json';runner=out/'verify-runner.sh';assert not resultfile.exists() and not runner.exists()
before=json.loads((P/'local/hardware/armbian-official-g6-r5-20261030-01/ssh-before-charger.json').read_text())
code='''import hashlib,json,os,subprocess,time
from pathlib import Path
expected=EXPECTED
actual={n:hashlib.sha256((Path('/usr/libexec/f8-pro')/n).read_bytes()).hexdigest() for n in expected}
assert actual==expected,'Running payload does not match r6 image'
boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip()
assert boot!=OLD_BOOT,'Still the previous boot'
observations=[]
for index in range(3):
    data=json.loads(Path('/run/f8/power-current.json').read_text())
    age=time.monotonic()-data['monotonic_seconds']
    assert data['complete'] and 'adc_refresh' in data and 0<=age<25
    observations.append({'register_age_seconds':age,'snapshot_seconds':data['monotonic_seconds'],
      'adc_refresh':data['adc_refresh'],'bq':data['devices']['0x6a']['decoded'],'cw':data['devices']['0x62']['decoded']})
    if index<2:time.sleep(11)
def command(args):
    r=subprocess.run(args,capture_output=True,text=True,timeout=6)
    return {'exit':r.returncode,'stdout':r.stdout,'stderr':r.stderr}
print(json.dumps({'scope':'G6 r6 authenticated cold-boot payload and sampler verification',
 'boot_id':boot,'new_boot_verified':True,'kernel':os.uname().release,'payload_hashes':actual,
 'observations':observations,'old_ram_backup_present':Path('/run/f8/power-refresh-before-01').exists(),
 'services':command(['systemctl','show','f8-live-prepare','f8-live-network','f8-live-ssh','f8-live-power','f8-live-status',
 'f8-official-graphics','f8-official-wayland','-p','Id','-p','ActiveState','-p','SubState','-p','Result','-p','ExecMainStatus']),
 'failed_units':command(['systemctl','--no-pager','--failed']),
 'gpu':json.loads(Path('/run/f8/gpu-result.json').read_text()),'mounts':Path('/proc/mounts').read_text()},indent=2))
'''.replace('EXPECTED',repr(expected)).replace('OLD_BOOT',repr(before['boot_id']))
runner.write_text("set -eu\ntest \"$(uname -r)\" = 6.1.115-vendor-rk35xx\npython3 -I - <<'F8_VERIFY_PY'\n"+code+'\nF8_VERIFY_PY\n')
r=subprocess.run(['python3',str(P/'tools/ssh-f8-live.py'),'--address','192.168.1.227','--script',str(runner),'--sudo'],capture_output=True,text=True,timeout=80)
assert r.returncode==0,r.stderr[-1800:]
data=json.loads(r.stdout);data['collector_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
with resultfile.open('x') as stream:stream.write(json.dumps(data,indent=2)+'\n')
summary={'new_boot':data['new_boot_verified'],'r6_hashes_match':True,'old_ram_backup_present':data['old_ram_backup_present'],
 'gpu_hardware_accepted':data['gpu']['hardware_accepted'],'samples':[{'fresh':s['adc_refresh']['fresh'],
 'adc_age':s['adc_refresh'].get('age_seconds'),'input':s['bq']['power_good'],
 'charge_ma_estimate':s['bq']['battery_charge_current_ma_estimate'],
 'battery_uv':s['bq']['battery_adc_uv'],'soc':s['cw']['soc_raw_percent']} for s in data['observations']],
 'failed':data['failed_units']['stdout'],'services':data['services']['stdout']}
print(json.dumps(summary,indent=2))
