"""Create an audited BOOT+16GiB ROOTFS archive from a private sanitized snapshot."""
from pathlib import Path
import sys,os,json,struct,gzip,hashlib,subprocess,zipfile,importlib.util,time,shutil,re
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'tools'))
from inspect_images import fdt
B=Path('/var/tmp/f8-pro-armbian/release-20261103-r2');R=B/'rootfs';O=P/'outputs/armbian/f8-armbian-20261103-r2';O.mkdir(parents=True,exist_ok=True)
assert (B/'configured.json').exists() and (B/'privacy-audit.json').exists()
assert not (O/'bundle.json').exists(),'Preserve a completed release'
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def progress(phase,**data):(B/'progress.json').write_text(json.dumps({'phase':phase,'time':time.time(),**data})+'\n');print(phase,flush=True)
raw=(B/'BOOT_CURRENT_PARTITION.img').read_bytes();tree=fdt(raw);total=struct.unpack_from('>I',raw,4)[0];assert raw[:4]==b'\xd0\x0d\xfe\xed'
boot=bytearray(len(raw));boot[:total]=raw[:total];parts={};ranges=[]
for path,item in tree.items():
 if not path.startswith('/images/') or path.count('/')!=2:continue
 name=path.rsplit('/',1)[1]
 if 'data-position' not in item:continue
 start=int.from_bytes(item['data-position'],'big');length=int.from_bytes(item['data-size'],'big');assert total<=start<start+length<=len(raw)
 assert all(start+length<=a or start>=b for a,b in ranges);ranges.append((start,start+length));data=raw[start:start+length]
 hashes=[v for k,v in tree.items() if k.startswith(path+'/hash') and v.get('algo',b'').rstrip(b'\0')==b'sha256']
 assert hashes and all(hashlib.sha256(data).digest()==h['value'] for h in hashes),name
 boot[start:start+length]=data;parts[name]=data
assert {'kernel','fdt','ramdisk','resource'}<=parts.keys()
assert hashlib.sha256(parts['kernel']).hexdigest()=='a67daf71caefef6b97a22ba708bbb302b239a4a9b4874cadd17a217ebd0c37b7'
uuid='69056675-4a48-4006-a3f3-5132c00cc6f2';dt=fdt(parts['fdt']);assert ('root=UUID='+uuid).encode() in dt['/chosen']['bootargs']
spec=importlib.util.spec_from_file_location('boot_cpio',P/'tools/build-usb-bootlog.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
cpio=m.cpio_read(gzip.decompress(parts['ramdisk']));assert uuid.encode() in dict((n,b) for n,v,b in cpio)['init']
for n,v,b in cpio:
 assert not re.search(rb'(?im)^\s*(?:psk|wpa-psk|wep-key[0-3])\s*=\s*[^\s#]+',b),n
 assert not any(x in b for x in [b'-----BEGIN OPENSSH PRIVATE KEY-----',b'-----BEGIN RSA PRIVATE KEY-----',b'-----BEGIN PRIVATE KEY-----']),n
bootpath=O/'BOOT_F8_ARMBIAN_20261103_R2.img';bootpath.write_bytes(boot)
progress('building_rootfs_image')
image=B/'ROOTFS_F8_ARMBIAN_20261103_R2.ext4.img';size=16*1024**3
if image.exists():assert (B/'current-mkfs-complete.json').exists(),'Inspect incomplete mkfs'
else:
 with image.open('xb') as f:f.truncate(size)
 with (O/'mkfs.log').open('w') as log:subprocess.run(['mkfs.ext4','-F','-L','F8_ARMBIAN_R2','-U',uuid,'-O','^orphan_file','-E','lazy_itable_init=0,lazy_journal_init=0','-d',str(R),str(image)],stdout=log,stderr=subprocess.STDOUT,check=True)
 (B/'current-mkfs-complete.json').write_text(json.dumps({'bytes':size})+'\n')
progress('checking_rootfs_image')
with (O/'fsck.log').open('w') as log:subprocess.run(['e2fsck','-fn',str(image)],stdout=log,stderr=subprocess.STDOUT,check=True)
assert subprocess.check_output(['blkid','-s','UUID','-o','value',str(image)],text=True).strip()==uuid
checks=json.loads((B/'configured.json').read_text())['critical_files']
for pkg in ['f8-sensor-relay-r2','f8-fcitx5-r1']:
 fn='installation-manifest.json' if pkg.endswith('relay-r2') else 'manifest.json'
 d=json.loads((P/'outputs/armbian'/pkg/fn).read_text())
 for n,info in d['files'].items():
  p=R/n;assert p.is_file() and sha(p)==info['sha256'],n;checks['/'+n]=info['sha256']
for n in ['etc/passwd','etc/shadow','etc/ssh/sshd_config','etc/netplan/00-default-use-network-manager.yaml','etc/skel/.config/fcitx5/conf/pinyin.conf','etc/skel/.config/fcitx5/conf/cloudpinyin.conf','usr/lib/aarch64-linux-gnu/fcitx5/libcloudpinyin.so','etc/systemd/system/ssh.service.d/10-f8-new-hostkeys.conf']:
 checks['/'+n]=sha(R/n)
readback=B/'readback';readback.mkdir(exist_ok=True)
for i,(n,h) in enumerate(checks.items()):
 canonical='/'+str((R/n.lstrip('/')).resolve().relative_to(R));dst=readback/str(i)
 subprocess.run(['debugfs','-R',f'dump {canonical} {dst}',str(image)],check=True,capture_output=True);assert sha(dst)==h,n
for n in ['/etc/NetworkManager/system-connections','/etc/ssh','/home']:
 text=subprocess.check_output(['debugfs','-R','ls -p '+n,str(image)],stderr=subprocess.DEVNULL,text=True)
 if n.endswith('system-connections'):assert not any(x for x in text.splitlines() if x and x.split('/')[5] not in ['.','..'])
 if n=='/etc/ssh':assert 'ssh_host_' not in text
 if n=='/home':assert '/f8setup/' in text and '/likimk/' not in text
privacy=json.loads((B/'privacy-audit.json').read_text());progress('hashing_image')
record={'version':'F8 Armbian 20261103 R2','root_file':image.name,'root_bytes':size,'root_sha256':sha(image),'root_uuid':uuid,'boot_file':bootpath.name,'boot_bytes':len(boot),'boot_sha256':sha(bootpath),'boot_payloads_identical_to_running_tablet':True,'unused_boot_partition_bytes_zeroed':True,'source_boot_partition_sha256':hashlib.sha256(raw).hexdigest(),'boot_lba':'0x00008000','root_lba':'0x00078000','partition_table_change':False,'privacy':privacy,'critical_files_readback':checks,'filesystem_check_passed':True,'cloudpinyin_backend':'Baidu','cold_boot_tested':False,'fresh_install_tested':False}
(O/'manifest.json').write_text(json.dumps(record,indent=2)+'\n');shutil.copyfile(B/'privacy-audit.json',O/'privacy-audit.json')
readme='''F8 RK3588S 平板 Armbian 测试包 · 2026-11-03 R2

包含当前已验证BOOT及16GiB ROOTFS（首次启动继续按既有服务扩展到分区容量）。
首次开机图形向导新建账户，没有默认登录密码。Wi-Fi配置/密码、SSH主机及用户密钥/known_hosts、旧账户与个人目录均已清除；SSH默认关闭，手动启用时生成新主机密钥。
已包含Fcitx5中文屏幕键盘/实体键盘、百度云拼音及目前已适配的平板功能、浏览器姿态R2。云拼音会联网发送拼音查询；可在Fcitx5拼音设置关闭。

刷写会覆盖现有系统和账户，请先备份个人文件。本任务只制作文件，没有刷写设备。
RKDevTool Loader模式：BOOT写0x00008000，ROOTFS写0x00078000。仅勾选这两行，不刷Loader/uboot/分区表。必须沿用当前F8分区布局；没有制作覆盖任意设备的通用升级固件。
ZIP中ROOTFS解压后为16GiB，请预留足够空间。先按SHA256SUMS核对文件。
BOOT载荷与当前实机一致，只清零无用分区间隙/尾部；ROOTFS已fsck及关键文件回读。尚未进行这份完整包的实际新刷/冷启动验收，首次开机向导和扩容需在新刷后确认。
详见项目docs/armbian-release-20261103-r2.md。
'''
(O/'README-刷入说明.txt').write_text(readme,encoding='utf-8')
(O/'SHA256SUMS').write_text(record['boot_sha256']+'  '+bootpath.name+'\n'+record['root_sha256']+'  '+image.name+'\n')
progress('compressing_release')
archive=O/'F8_ARMBIAN_20261103_R2_BOOT_ROOTFS.zip'
with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=1,allowZip64=True) as z:
 for p in [bootpath,image,O/'manifest.json',O/'privacy-audit.json',O/'README-刷入说明.txt',O/'SHA256SUMS']:z.write(p,arcname=p.name)
progress('verifying_release_archive')
with zipfile.ZipFile(archive) as z:assert z.testzip() is None
bundle={'archive':archive.name,'bytes':archive.stat().st_size,'sha256':sha(archive),'zip_crc_check_passed':True,'manifest':'manifest.json'}
(O/'bundle.json').write_text(json.dumps(bundle,indent=2)+'\n');(O/'ZIP-SHA256.txt').write_text(bundle['sha256']+'  '+archive.name+'\n');progress('complete',bundle=bundle)
