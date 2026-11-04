"""Copy signed official root locally and validate its official Panthor switch."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

P=Path('/mnt/d/Netdisk/Other/F8-PRO/archlinux')
evidence=P/'analysis/armbian/official-gpu-baseline-20261029'
download=json.loads((evidence/'downloaded-desktop.json').read_text())
inspection=json.loads((evidence/'official-image-inspection.json').read_text())
assert download['signature_verified'] and download['image_extracted']
assert download['sha256']=='fae6bd998cf8bf75274a367f1f3937aae609d6560e3110df35434cf6a9a45612'
source=Path('/var/tmp/f8-pro-armbian/official-desktop-26.8.1/official.img')
assert source.stat().st_size==inspection['image_bytes']
work=Path('/var/tmp/f8-pro-armbian/f8-official-armbian-26.8.1')
work.mkdir(exist_ok=True)
mount=work/'source-readonly';mount.mkdir(exist_ok=True)
destination=work/'rootfs'
done=evidence/'prepared-official-root.json'
assert not done.exists(), 'Porting root already recorded; preserve existing work'
copy_record=evidence/'official-root-copy-complete.json'
if destination.exists():
    prior=json.loads(copy_record.read_text())
    assert prior['root_directory']==str(destination) and prior['source_image_sha256']==download['sha256']
    assert prior['cp_a_completed'] is True
assert subprocess.run(['mountpoint','-q',str(mount)]).returncode!=0
part=next(x for x in inspection['partitions'] if x['ext_magic']=='53ef')
options=f"ro,noload,loop,offset={part['start_lba']*512},sizelimit={(part['end_lba']-part['start_lba']+1)*512}"
if not destination.exists():
    subprocess.run(['mount','-t','ext4','-o',options,str(source),str(mount)],check=True)
    try:
        print('Copying official root locally with numeric ownership, modes and symlinks preserved',flush=True)
        subprocess.run(['cp','-a',str(mount),str(destination)],check=True)
    finally:
        subprocess.run(['umount',str(mount)],check=True)
    copy_record.write_text(json.dumps({'root_directory':str(destination),
        'source_image_sha256':download['sha256'],'cp_a_completed':True},indent=2)+'\n')
sys.path.insert(0,str(P/'tools'))
from inspect_images import fdt
base=evidence/'official-rk3588s-orangepi-5.dtb'
overlay=evidence/'image-overlays/rockchip-rk3588-panthor-gpu.dtbo'
result=evidence/'reference-orangepi5-panthor-enabled.dtb'
subprocess.run(['fdtoverlay','-i',str(base),'-o',str(result),str(overlay)],check=True)
nodes=fdt(result.read_bytes())
assert nodes['/gpu@fb000000']['status']==b'disabled\0'
panthor=nodes['/gpu-panthor@fb000000']
assert panthor['status']==b'okay\0'
assert b'arm,mali-valhall-csf\0' in panthor['compatible']
supply_path=nodes['/__symbols__']['vdd_gpu_s0'].decode().rstrip('\0')
assert panthor['mali-supply']==nodes[supply_path]['phandle']
libmali=[str(x.relative_to(destination)) for x in (destination/'usr/lib').rglob('*.so*') if x.name.lower().startswith('libmali')]
inspection['libmali_files']=libmali
(evidence/'official-image-inspection.json').write_text(json.dumps(inspection,indent=2)+'\n')
required=[destination/'boot/vmlinuz-6.1.115-vendor-rk35xx',
          destination/'usr/lib/modules/6.1.115-vendor-rk35xx/kernel/drivers/gpu/drm/panthor/panthor.ko',
          destination/'usr/lib/firmware/arm/mali/arch10.8/mali_csffw.bin']
assets=[{'path':str(x.relative_to(destination)), 'bytes':x.stat().st_size,
         'sha256':hashlib.sha256(x.read_bytes()).hexdigest()} for x in required]
assert assets[-1]['sha256']=='a27847ea11f8efb3136340c3ba8aab413ae25145eeb4a7f64ff5edd829a2405b'
report={'date':'2026-10-29','root_directory':str(destination),
        'source_image_sha256':download['sha256'],'official_version':'26.8.1',
        'source_root_copied_with_cp_a':True,'official_image_modified':False,
        'reference_panthor_overlay_applied':True,
        'reference_old_gpu_disabled':True,'reference_panthor_enabled':True,
        'reference_gpu_supply_phandle_verified':True,
        'reference_dtb_is_for_f8_pro':False,'libmali_libraries':libmali,
        'matching_official_assets':assets,
        'f8_hardware_adaptations_applied':False,'hardware_test_performed':False,
        'target_device_modified':False}
done.write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2),flush=True)
