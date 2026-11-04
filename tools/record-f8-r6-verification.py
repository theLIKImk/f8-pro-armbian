"""Mark cold-boot evidence only after authenticated r6 payload verification."""
import json
from pathlib import Path
P=Path(__file__).resolve().parents[1]
evidence=P/'local/hardware/armbian-official-g6-r6-20261030-01/boot-verification.json'
data=json.loads(evidence.read_text())
assert data['new_boot_verified'] and not data['old_ram_backup_present']
assert data['gpu']['hardware_accepted']
assert len(data['observations'])==3
assert all(s['adc_refresh']['fresh'] and s['adc_refresh']['configuration_unchanged'] for s in data['observations'])
assert len({s['snapshot_seconds'] for s in data['observations']})==3
assert '0 loaded units listed.' in data['failed_units']['stdout']
pf=P/'outputs/armbian/official-f8-live-g6-r6/preflight.json'
backup=pf.with_name('preflight-before-hardware.json')
if not backup.exists():backup.write_bytes(pf.read_bytes())
meta=json.loads(pf.read_text());meta.update(hardware_test_performed=True,r6_cold_boot_verified=True,
 wifi_ssh_verified=True,sampling_persistence_verified=True,user_reported_flashed=True,
 deployment_performed=True,deployment_method='User manually flashed boot; authenticated new boot payloads verified',
 hardware_result='local/hardware/armbian-official-g6-r6-20261030-01/boot-verification.json',charging_validated=False)
pf.write_text(json.dumps(meta,indent=2)+'\n')
print(json.dumps({'cold_boot_verified':True,'persistent_sampler_verified':True,
 'adc_age_seconds':[s['adc_refresh'].get('age_seconds') for s in data['observations']],
 'charge_current_estimates_ma':[s['bq']['battery_charge_current_ma_estimate'] for s in data['observations']],
 'gpu_hardware_accepted':True,'failed_units':0}))
