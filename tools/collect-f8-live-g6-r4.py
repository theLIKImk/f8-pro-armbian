"""Archive G6 r4 systemd report and missing-live-target evidence."""
import hashlib
import json
from pathlib import Path
import shutil
P=Path(__file__).resolve().parents[1];source=Path('F:/')
assert 'ARMBIAN-G6' in (source/'RESULT.TXT').read_text() and 'mode=systemd' in (source/'RESULT.TXT').read_text()
dest=P/'local/hardware/armbian-official-g6-r4-20261030-01';assert not dest.exists();dest.mkdir()
names=[p.name for p in (P/'local/hardware/armbian-official-g5-20261029-01').iterdir() if p.name!='test-result.json']
names+=['SETUP.TXT','LIVELOG.TXT','NETWORK.TXT','IP.TXT','PORTS.TXT','POWER2.JSON']
for name in names:
    if (source/name).is_file():shutil.copyfile(source/name,dest/name)
report={'scope':'G6 r4 reaches systemd but old target still active; live services not started',
 'date':'2026-10-30','systemd_boot_verified':True,'wifi_firmware_loaded':True,'wifi_dhcp_verified':False,
 'ssh_verified':False,'power_live_service_started':False,'automatic_old_popup_user_observed':True,
 'diagnosis':'Init asset case omitted *.target; new target copied to libexec instead of systemd directory',
 'files':[{'name':p.name,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(dest.iterdir())]}
(dest/'test-result.json').write_text(json.dumps(report,indent=2)+'\n')
pf=P/'outputs/armbian/official-f8-live-g6-r4/preflight.json';backup=pf.with_name('preflight-before-hardware.json')
if not backup.exists():backup.write_bytes(pf.read_bytes())
meta=json.loads(pf.read_text());meta.update(hardware_test_performed=True,systemd_boot_verified=True,
 live_services_started=False,hardware_result='local/hardware/armbian-official-g6-r4-20261030-01/test-result.json')
pf.write_text(json.dumps(meta,indent=2)+'\n')
print(json.dumps({'files_saved':len(report['files']),'systemd_boot_verified':True,'ssh_verified':False}))
