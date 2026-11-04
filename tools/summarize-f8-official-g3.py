"""Preserve measured G3 failure and verified G4 static metadata; no device writes."""
import hashlib
import json
from pathlib import Path
import re
import sys
P=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(P/'tools'))
from inspect_images import fdt
logs=P/'local/hardware/armbian-official-g3-20261029-01'
def read(name):return (logs/name).read_text(encoding='utf-8')
gpu=json.loads(read('GPU.JSON'));touch=json.loads(read('TOUCH.JSON'));dmesg=read('DMESG.TXT')
assert gpu['hardware_accepted'] and gpu['driver']=='panthor' and not gpu['software_renderer']
assert gpu['pixel_rgba']==[64,128,191,255] and gpu['gl_error']==0
assert not touch['device_found'] and touch['event_count']==0
assert 'timeout, ipd: 0x10, state: 3' in dmesg or 'timeout, ipd: 0x10, state: 3' in dmesg.replace('  ',' ')
assert 'GSL3673 test_i2c error!' in dmesg and 'failed with error -110' in dmesg
assert all(x in read('GRAPHICS.TXT') for x in ['TOUCH_MODULE_EXIT=0','WAYLAND_START=0','WAYLAND_STOP=0','TOUCH_CAPTURE_EXIT=1'])
report={'date':'2026-10-29','host_volume':'F: F8AG3','hardware_test_performed':True,
 'touch_hardware_accepted':False,'module_registered':True,'touch_driver_bound':False,
 'touch_result':touch,'failure':'First controller I2C test timed out (-110); probe removed temporary input device',
 'gpu_result':gpu,'system_state':read('SYSSTATE.TXT').strip(),
 'panic_or_oops_in_snapshot':bool(re.search(r'Kernel panic|Oops:',dmesg)),
 'diagnosis':'I2C4 pinctrl used m0 GPIO3_A5/A6; factory uses m3 GPIO1_A2/A3',
 'g4_hardware_fix_verified':False,'charging_tested':False,
 'files':[{'name':f.name,'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()}
          for f in sorted(logs.iterdir()) if f.name!='test-result.json']}
(logs/'test-result.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
base=P/'outputs/armbian/official-f8-touch-g3';pf=base/'preflight.json'
backup=base/'preflight-before-hardware.json'
if not backup.exists():backup.write_bytes(pf.read_bytes())
old=json.loads(pf.read_text());old.update(hardware_test_performed=True,touch_hardware_accepted=False,
 hardware_result='First I2C test timeout -110; see G3 test-result.json; superseded by G4 for retest')
pf.write_text(json.dumps(old,indent=2)+'\n')
g4=P/'outputs/armbian/official-f8-touch-g4';pf=g4/'preflight.json';meta=json.loads(pf.read_text())
blob=(g4/meta['candidate_file']).read_bytes();assert hashlib.sha256(blob).hexdigest()==meta['candidate_sha256']
tree=fdt(blob);hashes={}
for name in ['kernel','fdt','ramdisk','resource']:
 props=tree['/images/'+name];start=int.from_bytes(props['data-position'],'big');size=int.from_bytes(props['data-size'],'big')
 digest=hashlib.sha256(blob[start:start+size]).digest();assert digest==tree['/images/'+name+'/hash']['value']
 hashes[name]=digest.hex()
meta['payload_sha256']=hashes
meta['touch_dt_only_changes']=['I2C4 pinctrl-0','add factory m3 pin group']
pf.write_text(json.dumps(meta,indent=2)+'\n')
print(json.dumps({'g3_touch_accepted':False,'g3_gpu_accepted':True,'g4_sha256':meta['candidate_sha256']}))
