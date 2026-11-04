"""Freeze a separate official-Armbian GPU/display trial SquashFS, never deploy."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

P=Path('/mnt/d/Netdisk/Other/F8-PRO/archlinux')
E=P/'analysis/armbian/official-gpu-baseline-20261029'
root=Path(json.loads((E/'prepared-official-root.json').read_text())['root_directory'])
checks=json.loads((E/'graphics-binding-check.json').read_text())
assert not checks['binding_differences'] and not checks['new_dtc_warnings'] and checks['wayland_cli_ready']
integration=json.loads((E/'graphics-root-integration.json').read_text())
assert integration['qemu_arm64_no_gpu_rejected']['hardware_accepted'] is False
assert integration['cpufreq_blacklist_symbol_in_official_map']
out=P/'outputs/armbian/official-f8-graphics-r1b'
assert not (out/'rootfs-manifest.json').exists(),'Preserve frozen image'
assets=P/'armbian/official-graphics'
for name in ['f8-official-report.service','f8-official-report.timer']:
    dest=root/'etc/systemd/system'/name
    if dest.exists():assert dest.read_bytes()==(assets/name).read_bytes()
    else:dest.write_bytes((assets/name).read_bytes())
    dest.chmod(0o644)
dest=root/'usr/libexec/f8-pro/graphics-report'
if dest.exists():assert dest.read_bytes()==(assets/'report.sh').read_bytes()
else:dest.write_bytes((assets/'report.sh').read_bytes())
dest.chmod(0o755)
subprocess.run(['chroot',str(root),'/bin/sh','-n','/usr/libexec/f8-pro/graphics-report'],check=True,timeout=30)
unitnames=['f8-official-graphics.target','f8-official-graphics.service','f8-official-wayland.service',
           'f8-official-report.timer','f8-official-report.service']
verify=subprocess.run(['systemd-analyze','--root='+str(root),'--man=no','verify',*unitnames],capture_output=True,text=True)
(E/'graphics-full-units-verify.log').write_text(verify.stdout+verify.stderr)
assert verify.returncode==0,verify.stderr
for name in ['machine-id']:
    assert not (root/'etc'/name).read_bytes()
assert not list((root/'etc/ssh').glob('ssh_host_*_key*'))
for path in ['proc','sys','dev','run']:
    assert subprocess.run(['mountpoint','-q',str(root/path)]).returncode!=0
toolroot=Path('/var/tmp/f8-pro-armbian/host-tools/root')
mksq=shutil.which('mksquashfs') or str(toolroot/'usr/bin/mksquashfs')
unsq=shutil.which('unsquashfs') or str(toolroot/'usr/bin/unsquashfs')
env=dict(os.environ)
if str(toolroot) in mksq:
    env['LD_LIBRARY_PATH']=str(toolroot/'usr/lib/x86_64-linux-gnu')+':'+str(toolroot/'lib/x86_64-linux-gnu')
image=out/'rootfs.squashfs';assert not image.exists()
print('Packing official KDE root with matched kernel/modules/firmware; no target writes',flush=True)
with (E/'graphics-squashfs-build.log').open('w') as log:
    subprocess.run([mksq,str(root),str(image),'-noappend','-comp','gzip','-processors','2','-no-progress',
                    '-wildcards','-e','proc/*','sys/*','dev/*','run/*','tmp/*','var/log/*',
                    'var/cache/apt/archives/*.deb','var/lib/apt/lists/*'],env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
summary=subprocess.check_output([unsq,'-s',str(image)],env=env,text=True)
(E/'graphics-squashfs-summary.txt').write_text(summary)
sha=hashlib.file_digest(image.open('rb'),'sha256').hexdigest()
(out/'SHA256SUMS').write_text(sha+'  rootfs.squashfs\n')
unit_hashes={n:hashlib.sha256((root/'etc/systemd/system'/n).read_bytes()).hexdigest() for n in unitnames}
report={'scope':'Official Armbian 26.8.1 KDE root plus bounded F8 GPU/Wayland trial changes; target untested',
        'project_relative_path':image.relative_to(P).as_posix(),'bytes':image.stat().st_size,'sha256':sha,
        'kernel_release':'6.1.115-vendor-rk35xx','original_official_gpu_assets_preserved':True,
        'rootfs_readback_summary_checked':True,'full_target_unit_graph_verified':True,'unit_sha256':unit_hashes,
        'machine_id_empty':True,'ssh_hostkeys_absent':True,'physical_fstab_empty':True,
        'root_image_staged_on_tablet':False,'hardware_test_performed':False}
(out/'rootfs-manifest.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2),flush=True)
