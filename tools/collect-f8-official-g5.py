"""Archive G5 fixed report whitelist and passive power evidence, no device writes."""
import hashlib
import json
from pathlib import Path
import re
import shutil
P=Path(__file__).resolve().parents[1];source=Path('F:/')
dest=P/'local/hardware/armbian-official-g5-20261029-01'
assert 'ARMBIAN-G5' in (source/'RESULT.TXT').read_text()
assert not dest.exists(),'Preserve previous collection'
names=[p.name for p in (P/'local/hardware/armbian-official-g4-20261029-01').iterdir()
       if p.name!='test-result.json']+['POWER0.JSON','POWER1.JSON','POWER0.TXT','POWERLOG.TXT','POWERBUS.TXT']
assert len(names)==45 and len(set(names))==45
for name in names:assert (source/name).is_file(),name
dest.mkdir()
for name in names:shutil.copyfile(source/name,dest/name)
early=json.loads((dest/'POWER0.JSON').read_text());late=json.loads((dest/'POWER1.JSON').read_text())
gpu=json.loads((dest/'GPU.JSON').read_text());touch=json.loads((dest/'TOUCH.JSON').read_text())
for snap in [early,late]:
    assert snap['complete'] and snap['register_value_writes']==0 and snap['fault_reg_0c_skipped']
    assert snap['physical_bus_verified'].endswith('/i2c@fec80000')
    assert all(v['read_complete'] for v in snap['devices'].values())
    assert snap['devices']['0x6a']['decoded']['part_number_code']==3
    assert snap['devices']['0x62']['decoded']['profile_equals_factory']
assert gpu['hardware_accepted'] and not gpu['software_renderer']
report={'date':'2026-10-29','scope':'G5 real I2C6 m3 BQ/CW passive reads, not charging control acceptance',
 'i2c6_factory_mux_hardware_verified':True,'early_seconds':early['monotonic_seconds'],
 'late_seconds':late['monotonic_seconds'],
 'bq_raw_unchanged_between_snapshots':early['devices']['0x6a']['raw']==late['devices']['0x6a']['raw'],
 'bq_early':early['devices']['0x6a']['decoded'],'bq_late':late['devices']['0x6a']['decoded'],
 'cw_early':early['devices']['0x62']['decoded'],'cw_late':late['devices']['0x62']['decoded'],
 'gpu_hardware_accepted':gpu['hardware_accepted'],'touch_device_found':touch['device_found'],
 'panic_or_oops_in_snapshot':bool(re.search(r'Kernel panic|Oops:',(dest/'DMESG.TXT').read_text())),
 'charging_control_validated':False,'pd_charger_tested':False,'adc_freshness_verified':False,
 'caveats':['Charge enable and current settings do not prove actual charge current',
 'All BQ registers identical including ADC; no new ADC conversion requested',
 'Raw VREG=4.4V documents current chip configuration, not complete vendor policy',
 'Input limit=3A is not evidence USB source can supply 3A'],
 'files':[{'name':p.name,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
          for p in sorted(dest.iterdir())]}
(dest/'test-result.json').write_text(json.dumps(report,indent=2)+'\n')
pf=P/'outputs/armbian/official-f8-power-g5/preflight.json';backup=pf.with_name('preflight-before-hardware.json')
if not backup.exists():backup.write_bytes(pf.read_bytes())
meta=json.loads(pf.read_text());meta.update(hardware_test_performed=True,power_readout_hardware_verified=True,
 hardware_result='local/hardware/armbian-official-g5-20261029-01/test-result.json')
pf.write_text(json.dumps(meta,indent=2)+'\n')
print(json.dumps({'files_copied':len(names),'early_seconds':report['early_seconds'],'late_seconds':report['late_seconds'],
 'bq_unchanged':report['bq_raw_unchanged_between_snapshots'],'cw_profile_matches':True,'gpu_accepted':True}))
