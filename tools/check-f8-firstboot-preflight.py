"""Final offline trial preflight. Does not authorize or perform deployment."""
import hashlib
import argparse
import json
from pathlib import Path
import shutil
import struct
import sys
P=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(P/'tools'))
from inspect_images import fdt
parser=argparse.ArgumentParser()
parser.add_argument('--revision',choices=['first','r2','r3','r4','r5'],default='first')
args=parser.parse_args()
is_r3=args.revision=='r3'
is_r5=args.revision=='r5'
is_r4=args.revision in ['r4','r5']
is_r2=args.revision in ['r2','r3','r4','r5']
out=P/'outputs/armbian'/('firstboot-diagnostic' if args.revision=='first' else 'firstboot-diagnostic-'+args.revision)
report=json.loads((out/'manifest.json').read_text())
backup_dir=P/'outputs/armbian/firstboot-diagnostic'
rollback=json.loads((backup_dir/'rollback-manifest.json').read_text())
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
image=out/('F8-PRO-6.1-'+args.revision.upper()+'-NOT-APPROVED.img' if is_r2 else 'F8-PRO-6.1-FIRSTBOOT-NOT-APPROVED.img')
backup=backup_dir/rollback['file']
assert sha(image)==report['image_sha256'] and sha(backup)==rollback['sha256']
assert rollback['remote_partition_sha256_matches'] and rollback['bytes']==64*1024*1024
phy=(out/'phy-rockchip-inno-usb2.source.txt').read_text()
for anchor in ['of_usb_get_dr_mode_by_phy(child_np, -1)',
               'ID must not change the role of a fixed peripheral.',
               'if (rport->mode == USB_DR_MODE_PERIPHERAL)',
               'case PHY_MODE_USB_DEVICE:']:
    assert anchor in phy
handoff=json.loads((P/'analysis/armbian/loader-placeholder/verified-handoff-paths.json').read_text())
live=json.loads((P/'analysis/armbian/live-loader-placement-2026-10-29.json').read_text())
raw=image.read_bytes();fit=fdt(raw)
if is_r2:
    node=fit['/images/fdt']
    start=int.from_bytes(node['data-position'],'big');size=int.from_bytes(node['data-size'],'big')
    dt=fdt(raw[start:start+size])
    command_line=dt['/chosen']['bootargs'].decode().strip('\0').split()
    assert 'initcall_blacklist=rockchip_cpufreq_driver_init' in command_line
    assert 'cpufreq.off=1' in command_line
    assert ('maxcpus=1' in command_line)==(not (is_r3 or is_r4))
    if is_r4:assert 'systemd.unit=f8-evaluation.target' in command_line
    assert dt['/i2c@fd880000']['pinctrl-0']==dt['/pinctrl/i2c0/i2c0m2-xfer']['phandle']
oldfit=fdt(backup.read_bytes())
oldrd=int.from_bytes(oldfit['/images/ramdisk']['data-size'],'big')
chosen=live['chosen_initrd']
assert oldrd==int(chosen['linux,initrd-end']['physical_address'],16)-int(chosen['linux,initrd-start']['physical_address'],16)
kernel=P/'outputs/armbian/evaluation-kernel/Image'
runtime=struct.unpack_from('<Q',kernel.read_bytes(),16)[0]
fdt_size=int.from_bytes(fit['/images/fdt']['data-size'],'big')+handoff['dt_expansion_bytes']
rdsize=int.from_bytes(fit['/images/ramdisk']['data-size'],'big')
observed=handoff['old_running_kernel_observation']
addresses={'kernel':int(observed['kernel_code_start'],16),
           'initrd':int(observed['initrd_start'],16),'dtb':0x08300000}
ranges={name:(addresses[name],addresses[name]+size) for name,size in [('kernel',runtime),('initrd',rdsize),('dtb',fdt_size)]}
memory=json.loads((P/'analysis/armbian/live-memory-baseline.json').read_text())
banks=[(int(row['base'],16),int(row['base'],16)+int(row['size'],16)) for row in memory['banks']]
for name,(start,end) in ranges.items():assert any(a<=start<end<=b for a,b in banks),name
for name,(start,end) in ranges.items():
    for other,(a,b) in ranges.items():
        if other!=name:assert not(start<b and a<end),(name,other)
assert addresses['kernel']%(2*1024*1024)==0 and addresses['dtb']%8==0 and fdt_size<=2*1024*1024
final=out/('BOOT_ONLY_6.1_DIAGNOSTIC_'+args.revision.upper()+'_CANDIDATE.img' if is_r2 else 'BOOT_ONLY_6.1_FIRSTBOOT_CANDIDATE.img')
shutil.copyfile(image,final)
assert sha(final)==report['image_sha256']
result={'scope':'Offline readiness for user-coordinated first hardware trial, not proof of successful boot',
    'revision':args.revision,
    'candidate_file':final.name,'candidate_bytes':final.stat().st_size,'candidate_sha256':sha(final),
    'rollback_file':backup.name,'rollback_sha256':rollback['sha256'],
    'rollback_project_relative_path':backup.relative_to(P).as_posix(),
    'backup_validation_scope':'Saved original BOOT before first trial; not a fresh readback of current diagnostic partition',
    'current_partition_backup_verified':True,'old_initrd_span_matches_backup_payload_size':True,
    'usb_fixed_peripheral_source_reviewed':True,'usb_phy_hardware_behavior_verified':False,
    'layout_screened':{n:{'start':hex(a),'end_exclusive':hex(b)} for n,(a,b) in ranges.items()},
    'dt_expansion_included_bytes':handoff['dt_expansion_bytes'],
    'geometry_nonoverlap_passed':True,'dt_address_is_embedded_default_not_live_measurement':True,
    'new_kernel_actual_placement_verified':False,'hardware_test_performed':False,
    'ready_for_user_coordinated_trial':True,'deployment_authorized':False,
    'test_scope':['Kernel reaches diagnostic init','eMMC enumerates','Read-only RAM log disk enumerates over USB'],
    'no_desktop_or_rootfs_mount':True,
    'desktop_will_start':False,'original_rootfs_mount_planned':is_r3 or is_r4,
    'remaining_trial_uncertainties':['Loader acceptance of new payloads','Final loader DT selection/fixups',
                                   'New-kernel PMIC/storage initialization','USB2 PHY and host enumeration']}
if is_r2:
    result['test_scope']=['I2C0 mux conflict absent','RK8602/3 regulators bind',
                          'Vendor cpufreq initcall actually skipped','Read-only regulator/pinmux/CPU logs']
    result['remaining_trial_uncertainties']=['Regulator binding and hardware readback after mux fix',
                                           'Actual initcall blacklist effect','Original regulator device-link warnings']
if is_r3:
    result['test_scope']=['All 8 CPUs online without vendor DVFS init','UART2 serial console registered',
                         'Original Arch root mounts ro,noload','Original true/systemd --version execute']
    result['no_desktop_or_rootfs_mount']=False
    result['rootfs_mount_policy']='PARTUUID-checked ro,noload; no PID1/services'
    result['remaining_trial_uncertainties']=['SMP bringup under retained firmware clock settings',
                                           'Serial console registration','Readonly filesystem and basic userspace execution']
if is_r4:
    staging=json.loads((P/'analysis/armbian/userspace/tablet-rootfs-staging.json').read_text())
    assert staging['sha256']=='a69fdacdc7ad5fc1d9239ffb271c40bb2e05fb151e0635c2f59b2ef70885a8dc'
    checks=json.loads((out/'userspace-precheck.json').read_text())
    assert checks['ramdisk_sha256']==report['ramdisk_sha256']
    assert checks['packed_init_and_logger_match_sources']
    assert len(checks['move_rollback_fixtures'])==5 and all(x['passed'] for x in checks['move_rollback_fixtures'])
    assert len(checks['target_units_verified'])==3
    if is_r5:
        assert checks['nonroot_directory_permission_fixture_passed']
        assert checks['packed_permission_policy_verified']
    result['test_scope']=['Verified staged SquashFS mounted read-only','RAM overlay becomes root',
                         'Trixie systemd runs as PID1','Basic evaluation target and timed USB report']
    result['no_desktop_or_rootfs_mount']=False
    result['rootfs_mount_policy']='Original Arch ro,noload; SquashFS read-only; overlay upper/work in tmpfs'
    result['remaining_trial_uncertainties']=['Target systemd PID1 startup','Unit/timer activation and USB export',
                                           'All writes remaining on RAM overlay']
    if is_r5:
        result['test_scope'] += ['Overlay root mode 0755 and units mode 0644',
                                 'Nonroot service reads os-release',
                                 'Resolved service no longer fails with CHDIR']
        result['remaining_trial_uncertainties']=['Live overlay permission metadata',
                                               'Resolved and nonroot probe status',
                                               'R5 timed USB snapshot export']
(out/'preflight.json').write_text(json.dumps(result,indent=2)+'\n')
report['offline_preflight_complete']=True
report['pending']=['User-coordinated boot-only first hardware trial; no deployment yet']
(out/'manifest.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(result,indent=2))
