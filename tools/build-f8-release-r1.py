"""Build and verify an offline 12GiB first-run image; never flash a device."""
from pathlib import Path
import gzip,hashlib,importlib.util,json,os,shutil,subprocess,sys,time,zipfile
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'tools'))
from inspect_images import fdt
from f8_resource_image import parse
B=Path('/var/tmp/f8-pro-armbian/release-r1');R=B/'rootfs';O=P/'outputs/armbian/f8-armbian-r1';O.mkdir(exist_ok=True)
assert (B/'configured.json').exists() and (B/'first-run-native-test.json').exists()
assert not (O/'bundle.json').exists(),'Preserve a completed bundle'
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
root_uuid='69056675-4a48-4006-a3f3-5132c00cc6f2'
source=P/'outputs/armbian/official-f8-camera-c4/BOOT_ONLY_ARMBIAN_CAMERA_C4.img'
assert sha(source)=='fbbfa1ece55b3c62decbd10ae9c2ac98ed5d717dd5f8b941c49004deb6c0903a'
blob=source.read_bytes();tree=fdt(blob);payload={}
for name in ['kernel','fdt','ramdisk','resource']:
 item=tree['/images/'+name];a=int.from_bytes(item['data-position'],'big');n=int.from_bytes(item['data-size'],'big');payload[name]=blob[a:a+n]
 assert hashlib.sha256(payload[name]).digest()==tree['/images/'+name+'/hash']['value']
assert hashlib.sha256(payload['kernel']).hexdigest()=='a67daf71caefef6b97a22ba708bbb302b239a4a9b4874cadd17a217ebd0c37b7'
assert parse(payload['resource'])['rk-kernel.dtb']==payload['fdt']
cmd=fdt(payload['fdt'])['/chosen']['bootargs'].decode().rstrip('\0');assert 'root=UUID='+root_uuid in cmd
assert 'cpufreq.off=1' in cmd and 'rkcif_clr_unready_dev,rkisp_clr_unready_dev' in cmd
s=importlib.util.spec_from_file_location('cpio',P/'tools/build-usb-bootlog.py');c=importlib.util.module_from_spec(s);s.loader.exec_module(c)
init=dict((n,b) for n,v,b in c.cpio_read(gzip.decompress(payload['ramdisk'])))['init']
assert root_uuid.encode() in init
# Image-level secret/account checks; source home directories were never imported.
assert (R/'etc/machine-id').read_bytes()==b''
assert not list((R/'etc/ssh').glob('ssh_host_*'))
assert not list((R/'etc/NetworkManager/system-connections').iterdir())
assert sorted(p.name for p in (R/'etc/netplan').iterdir())==['00-default-use-network-manager.yaml']
assert (R/'etc/netplan/00-default-use-network-manager.yaml').read_text()=='network:\n  version: 2\n  renderer: NetworkManager\n'
assert not (R/'usr/share/f8-pro/test-authorized-keys').exists()
assert sorted(x.name for x in (R/'home').iterdir())==['f8setup']
assert not (R/'var/lib/f8-pro/first-run/complete.json').exists()
assert 'f8test:' not in (R/'etc/passwd').read_text() and 'f8gpu:' not in (R/'etc/passwd').read_text()
assert all(x.split(':')[1]=='*' for x in (R/'etc/shadow').read_text().splitlines())
for name in ['etc/security/opasswd','etc/security/opasswd.old','etc/ppp/chap-secrets','etc/ppp/pap-secrets']:
 p=R/name;assert not p.exists() or p.read_bytes()==b'',name
for p in R.rglob('authorized_keys'):raise AssertionError('Unexpected authorization file: '+str(p))
image=B/'ROOTFS_F8_ARMBIAN_R1.ext4.img';size=12*1024**3
if image.exists():
 assert (B/'mkfs-complete.json').exists(),'Incomplete image needs inspection, not an automatic overwrite'
else:
 with image.open('xb') as f:f.truncate(size)
 print('Creating 12GiB ext4 image',flush=True)
 with (O/'mkfs.log').open('w') as log:
  subprocess.run(['mkfs.ext4','-F','-L','F8_ARMBIAN_R1','-U',root_uuid,'-O','^orphan_file','-E','lazy_itable_init=0,lazy_journal_init=0','-d',str(R),str(image)],stdout=log,stderr=subprocess.STDOUT,check=True)
 (B/'mkfs-complete.json').write_text(json.dumps({'bytes':size})+'\n')
with (O/'fsck.log').open('w') as log:subprocess.run(['e2fsck','-fn',str(image)],stdout=log,stderr=subprocess.STDOUT,check=True)
assert subprocess.check_output(['blkid','-s','UUID','-o','value',str(image)],text=True).strip()==root_uuid
# Read back important installed assets from the actual ext4, not just the staging tree.
checks=json.loads((B/'configured.json').read_text())['critical_files'];checks.update({x:sha(R/x.lstrip('/')) for x in ['/etc/sddm.conf.d/99-f8-first-run.conf','/etc/sudoers.d/f8-first-run','/etc/skel/.config/plasmakeyboardrc','/usr/local/lib/f8-pro/first-run.py','/usr/libexec/f8-pro/native-prepare.sh']})
extract=B/'verify-readback';extract.mkdir(exist_ok=True)
for i,(name,expected) in enumerate(checks.items()):
 path=extract/str(i)
 canonical='/'+str((R/name.lstrip('/')).resolve().relative_to(R))
 subprocess.run(['debugfs','-R',f'dump {canonical} {path}',str(image)],check=True,capture_output=True)
 assert path.is_file() and sha(path)==expected,name
print('Filesystem and critical-file readback passed; hashing root',flush=True)
root_sha=sha(image)
boot=O/'BOOT_F8_ARMBIAN_R1.img'
if not boot.exists():shutil.copyfile(source,boot)
assert sha(boot)==sha(source)
record={'version':'F8 Armbian R1 first-run test','root_file':image.name,'root_bytes':size,'root_sha256':root_sha,'root_uuid':root_uuid,'boot_file':boot.name,'boot_bytes':boot.stat().st_size,'boot_sha256':sha(boot),'boot_identical_to_validated_C4':True,'root_lba':'0x00078000','boot_lba':'0x00008000','partition_table_change':False,'fsck_passed':True,'critical_files_readback':checks,'first_run_arm64_integration_passed':True,'first_run_touch_keyboard_user_accepted':True,'packaged_cold_boot_verified':False,'target_partition_written':False,'source_copy_type':'live file snapshot excluding home/secrets; not a block-level backup'}
(O/'image-manifest.json').write_text(json.dumps(record,indent=2)+'\n')
for name,source_file in [('first-run-native-test.json',B/'first-run-native-test.json'),('root-integration.json',B/'configured.json')]:shutil.copyfile(source_file,O/name)
shutil.copyfile(P/'docs/flash-f8-armbian-r1.md',O/'刷入与首次设置.md')
(O/'SHA256SUMS').write_text(root_sha+'  '+image.name+'\n'+sha(boot)+'  '+boot.name+'\n')
partial=O/'F8_ARMBIAN_R1_TEST.zip.part';target=O/'F8_ARMBIAN_R1_TEST.zip'
assert not target.exists()
print('Compressing bundle',flush=True)
with zipfile.ZipFile(partial,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=3,allowZip64=True) as z:
 z.write(image,image.name)
 for name in [boot.name,'image-manifest.json','first-run-native-test.json','root-integration.json','刷入与首次设置.md','SHA256SUMS']:z.write(O/name,name)
(O/'zip-ready.json').write_text(json.dumps({'file':partial.name,'bytes':partial.stat().st_size,'closed':True})+'\n')
print('ZIP written; Windows native verification required before marking complete',flush=True)
