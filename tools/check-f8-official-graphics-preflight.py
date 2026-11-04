"""Verify actual packed tools/modules and publish a boot-only trial alias."""
import gzip
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'tools'))
from inspect_images import fdt
E=P/'analysis/armbian/official-gpu-baseline-20261029'
B=P/'outputs/armbian/official-f8-graphics-r1b'
O=B/'boot-g1b'
report=json.loads((O/'boot-manifest.json').read_text())
image=O/report['file'];assert hashlib.sha256(image.read_bytes()).hexdigest()==report['sha256']
root=Path(json.loads((E/'prepared-official-root.json').read_text())['root_directory'])
spec=importlib.util.spec_from_file_location('cpio_helper',P/'tools/build-usb-bootlog.py')
helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
records=helper.cpio_read(gzip.decompress((O/'initramfs.cpio.gz').read_bytes()))
contents={n:b for n,_,b in records}
assert hashlib.sha256(contents['f8-gpu-probe']).hexdigest()==report['ram_gpu_probe_override_sha256']
assert hashlib.sha256(contents['f8-evaluation-report']).hexdigest()==report['ram_report_override_sha256']
for name,expected in report['ram_wayland_helpers_sha256'].items():
    assert hashlib.sha256(contents['f8-'+name]).hexdigest()==expected
assert b'unset QT_QPA_PLATFORM DISPLAY WAYLAND_DISPLAY' in contents['f8-wayland-run']
assert b'export QT_QPA_PLATFORM=wayland' in contents['f8-wayland-client']
init=contents['init'].decode()
for required in ['chmod 0755 /run/f8-overlay/upper','mount -t ext4 -o ro,noload',
                 'sha256sum -c -','f8-official-graphics.target',report['rootfs_sha256'],
                 'cp /f8-gpu-probe /mnt/root/usr/libexec/f8-pro/gpu-probe.py',
                 'cp /f8-evaluation-report /mnt/root/usr/libexec/f8-pro/graphics-report']:
    assert required in init,required
work=Path('/var/tmp/f8-pro-armbian/official-graphics-boot-r1/packed-runtime');work.mkdir(exist_ok=True)
for name,fields,body in records:
    assert not Path(name).is_absolute() and '..' not in Path(name).parts
    path=work/name
    if stat.S_ISDIR(fields[1]):path.mkdir(parents=True,exist_ok=True);path.chmod(fields[1]&0o777)
    elif stat.S_ISREG(fields[1]):
        path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(body);path.chmod(fields[1]&0o777)
release='6.1.115-vendor-rk35xx'
env=dict(os.environ,QEMU_UNAME=release)
uname=subprocess.check_output(['chroot',str(work),'/bin/busybox','uname','-r'],env=env,text=True).strip()
assert uname==release,'QEMU target uname fixture must match actual target kernel release'
module_checks=[]
for name in ['squashfs','overlay']:
    result=subprocess.run(['chroot',str(work),'/bin/busybox','modprobe','-D','-v',name],env=env,capture_output=True,text=True)
    assert result.returncode==0,(name,result.stdout,result.stderr)
    assert name+'.ko' in result.stdout+result.stderr,(name,result.stdout,result.stderr)
    module_checks.append({'name':name,'show_dependencies_exit_code':result.returncode,'output':result.stdout+result.stderr})
for path in report['matching_initramfs_modules']:
    source=root/path
    assert source.read_bytes()==contents[path],path
blkid=subprocess.check_output(['chroot',str(work),'/sbin/blkid','--version'],text=True,timeout=30)
assert blkid.startswith('blkid ')
probe=root/'tmp/f8-packed-gpu-probe.py';output=root/'tmp/f8-packed-gpu-probe.json'
assert not probe.exists() and not output.exists()
probe.write_bytes(contents['f8-gpu-probe'])
try:
    result=subprocess.run(['chroot',str(root),'/usr/bin/python3','-I','/tmp/f8-packed-gpu-probe.py',
                           '--output','/tmp/f8-packed-gpu-probe.json'],capture_output=True,text=True,timeout=45)
    negative=json.loads(output.read_text())
    assert result.returncode==1 and negative['hardware_accepted'] is False
    assert 'Expected one Panthor render node' in negative['error']
finally:
    probe.unlink()
    if output.exists():output.unlink()
dt=fdt((O/'boot-graphics.NOT-APPROVED.dtb').read_bytes())
cmd=dt['/chosen']['bootargs'].decode().rstrip('\0').split()
assert 'systemd.unit=f8-official-graphics.target' in cmd and 'cma=256M' in cmd
assert 'initcall_blacklist=rockchip_cpufreq_driver_init' in cmd and 'maxcpus=1' not in cmd
assert dt['/gpu@fb000000']['status']==b'disabled\0'
assert dt['/gpu-panthor@fb000000']['status']==b'okay\0'
opps=[v for k,v in dt.items() if k.startswith('/gpu-panthor@fb000000/opp-table/') and v.get('status',b'okay\0')!=b'disabled\0']
assert len(opps)==1 and int.from_bytes(opps[0]['opp-hz'],'big')==200000000
staging=json.loads((E/'tablet-root-staging.json').read_text())
root_record=json.loads((B/'rootfs-manifest.json').read_text())
assert staging['sha256']==report['rootfs_sha256']==root_record['sha256']
assert staging['bytes']==root_record['bytes']
assert staging['remote_path']==report['rootfs_remote_path'] and staging['original_arch_ssh_confirmed']
final=O/'BOOT_ONLY_ARMBIAN_26.8.1_GPU_G1_CANDIDATE.img'
if final.exists():assert final.read_bytes()==image.read_bytes()
else:shutil.copyfile(image,final)
preflight={'scope':'Offline ready for coordinated official Armbian GPU/Wayland hardware trial; not hardware acceptance',
           'candidate_file':final.name,'candidate_bytes':final.stat().st_size,'candidate_sha256':report['sha256'],
           'root_sha256':root_record['sha256'],'root_staged_and_readback_verified':True,
           'packed_arm64_blkid_version':blkid.strip(),'packed_busybox_module_dependency_walks':module_checks,
           'modules_byte_equal_official_root':True,'packed_probe_no_device_rejection_verified':negative,
           'probe_api':'Mesa GBM surfaceless GLES3 RGBA8 FBO, 16x16 pixel readback',
           'gpu_max_test_hz':200000000,'initial_backlight_level':32,'log_volume':'F8AG1',
           'wayland_attempt_requires_hardware_gpu_probe':True,'wayland_duration_seconds':25,
           'original_root_mount_policy':'PARTUUID-checked ro,noload; official lower read-only; upper/work in RAM',
           'test_account':'f8gpu locked, no sudo','touch_enabled':False,'charging_enabled':False,
           'ready_for_user_coordinated_trial':True,'deployment_performed':False,'hardware_test_performed':False}
(O/'preflight.json').write_text(json.dumps(preflight,indent=2)+'\n')
report.update(scope=preflight['scope'],rootfs_staged=True,ready_for_user_flash=True,
              offline_preflight_complete=True,hardware_test_performed=False,
              remaining=['User-coordinated boot-only GPU/Wayland hardware trial and log capture'])
(O/'boot-manifest.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(preflight,indent=2))
