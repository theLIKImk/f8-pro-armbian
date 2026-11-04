"""Copy the known G4 report whitelist without changing the USB log disk."""
import hashlib
import json
from pathlib import Path
import re
import shutil
P=Path(__file__).resolve().parents[1]
source=Path('F:/');dest=P/'local/hardware/armbian-official-g4-20261029-01'
assert 'ARMBIAN-G4' in (source/'RESULT.TXT').read_text()
assert not dest.exists(),'Preserve previous collection'
names=[p.name for p in (P/'local/hardware/armbian-official-g3-20261029-01').iterdir()
       if p.name!='test-result.json']+['I2CBUS.TXT','KWINAPP.TXT','USERGFX.TXT']
dest.mkdir()
for name in names:
 assert (source/name).is_file(),name
 shutil.copyfile(source/name,dest/name)
gpu=json.loads((dest/'GPU.JSON').read_text());touch=json.loads((dest/'TOUCH.JSON').read_text())
assert gpu['hardware_accepted'] and not gpu['software_renderer']
assert touch['device_found'] and touch['event_count']>0
dm=(dest/'DMESG.TXT').read_text()
report={'date':'2026-10-29','scope':'G4 user confirms physical touch and GPU; captured event and EGL evidence',
 'gpu_result':gpu,'touch_result':touch,'user_confirmed_touch_works':True,
 'touch_events_captured':True,'charging_tested':False,'full_plasma_tested':False,
 'panic_or_oops_in_snapshot':bool(re.search(r'Kernel panic|Oops:',dm)),
 'files':[{'name':p.name,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
          for p in sorted(dest.iterdir())]}
(dest/'test-result.json').write_text(json.dumps(report,indent=2)+'\n')
pf=P/'outputs/armbian/official-f8-touch-g4/preflight.json'
backup=pf.with_name('preflight-before-hardware.json')
if not backup.exists():backup.write_bytes(pf.read_bytes())
meta=json.loads(pf.read_text());meta.update(hardware_test_performed=True,hardware_fix_verified=True,
 touch_hardware_accepted=True,hardware_result=str(dest.relative_to(P)/'test-result.json'))
pf.write_text(json.dumps(meta,indent=2)+'\n')
print(json.dumps({'files_copied':len(names),'event_count':touch['event_count'],
 'press_count':touch['press_count'],'max_active_contacts':touch['max_active_contacts'],
 'gpu_hardware_accepted':gpu['hardware_accepted']}))
