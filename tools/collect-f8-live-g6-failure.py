"""Preserve G6 init failure without changing the device or overwriting reports."""
import hashlib
import json
from pathlib import Path
import shutil
import argparse
parser=argparse.ArgumentParser();parser.add_argument('--revision',choices=['r2','r3'],default='r2');args=parser.parse_args()
P=Path(__file__).resolve().parents[1];source=Path('F:/')
assert 'ARMBIAN-G6' in (source/'RESULT.TXT').read_text()
assert 'mode=init-failed' in (source/'RESULT.TXT').read_text()
dest=P/('local/hardware/armbian-official-g6-'+args.revision+'-failure-20261029-01')
assert not dest.exists();dest.mkdir()
allowed=[p.name for p in (P/'local/hardware/armbian-official-g4-20261029-01').iterdir() if p.suffix=='.TXT']
for name in allowed:
    if (source/name).is_file():shutil.copyfile(source/name,dest/name)
steps=(dest/'STEPS.TXT').read_text()
if args.revision=='r2':
    assert 'nvram_ap6275p.txt' in steps and 'File exists' in steps
    failure='BusyBox cp -a could not replace existing firmware symlink'
else:
    assert 'rust-coreutils' in steps and 'auxv.rs' in steps
    failure='Target Rust coreutils aborted in early chroot auxiliary-vector initialization; likely chown, exact invocation not logged'
report={'scope':'G6 '+args.revision+' actual early-init failure, before systemd/SSH/status page',
 'failure':failure,
 'wifi_pcie_link_up':'PCIe Gen.1 x1 link up' in (dest/'DMESG.TXT').read_text(),
 'ssh_tested':False,'status_page_started':False,
 'files':[{'name':p.name,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
          for p in sorted(dest.iterdir())]}
(dest/'test-result.json').write_text(json.dumps(report,indent=2)+'\n')
pf=P/('outputs/armbian/official-f8-live-g6-'+args.revision+'/preflight.json')
backup=pf.with_name('preflight-before-hardware.json')
if not backup.exists():backup.write_bytes(pf.read_bytes())
meta=json.loads(pf.read_text());meta.update(hardware_test_performed=True,boot_failed=True,
 failure=report['failure'],hardware_result=str((dest/'test-result.json').relative_to(P)))
pf.write_text(json.dumps(meta,indent=2)+'\n')
print(json.dumps({'files_saved':len(report['files']),'wifi_pcie_link_up':report['wifi_pcie_link_up']}))
