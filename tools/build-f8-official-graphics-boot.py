"""Package official Image + F8 graphics DT + matched fs modules; never deploy."""
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import stat
import struct
import subprocess
import sys
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'tools'))
from inspect_images import fdt
E=P/'analysis/armbian/official-gpu-baseline-20261029'
BASE_OUT=P/'outputs/armbian/official-f8-graphics-r1b'
O=BASE_OUT/'boot-g1b';O.mkdir(exist_ok=True)
root=Path(json.loads((E/'prepared-official-root.json').read_text())['root_directory'])
root_record=json.loads((BASE_OUT/'rootfs-manifest.json').read_text())
assert not (O/'boot-manifest.json').exists(),'Preserve completed build'
work=Path('/var/tmp/f8-pro-armbian/official-graphics-boot-r1');work.mkdir(exist_ok=True)
release='6.1.115-vendor-rk35xx'
kernel=root/f'boot/vmlinuz-{release}'
assert hashlib.sha256(kernel.read_bytes()).hexdigest()=='a67daf71caefef6b97a22ba708bbb302b239a4a9b4874cadd17a217ebd0c37b7'
header=kernel.read_bytes()[:64]
assert header[56:60]==b'ARM\x64'
offset,runtime=struct.unpack_from('<QQ',header,8);assert offset==0 and runtime>=kernel.stat().st_size
cfg=(E/'official-image-kernel.config').read_text()
for name in ['EXT4_FS','BLK_DEV_LOOP','USB_DWC3','USB_DWC3_OF_SIMPLE','PHY_ROCKCHIP_INNO_USB2',
             'USB_GADGET','USB_LIBCOMPOSITE','USB_CONFIGFS','USB_CONFIGFS_MASS_STORAGE','VFAT_FS']:
    assert f'CONFIG_{name}=y\n' in cfg,name
assert 'CONFIG_KALLSYMS=y\n' in cfg
bindings=json.loads((E/'graphics-binding-check.json').read_text())
assert not bindings['binding_differences'] and not bindings['new_dtc_warnings']
spec=importlib.util.spec_from_file_location('cpio_helper',P/'tools/build-usb-bootlog.py')
helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
records=helper.cpio_read(gzip.decompress((P/'outputs/armbian/evaluation-initramfs-custom/initramfs-6.1.172-custom-DO-NOT-BOOT.cpio.gz').read_bytes()))
byname={n:(v,b) for n,v,b in records}
busybox=byname['bin/busybox'][1];(work/'busybox').write_bytes(busybox);(work/'busybox').chmod(0o755)
required=['sh','mount','umount','mkdir','cat','sleep','uname','ls','dmesg','cp','sync','head','ln',
          'timeout','sha256sum','switch_root','chmod','modprobe','insmod']
apps=subprocess.check_output(['qemu-aarch64-static',str(work/'busybox'),'--list'],text=True).splitlines()
assert set(required)<=set(apps)
new=[]
for name in ['dev','proc','sys','run','bin','dev/console','dev/null']:
    values,body=byname[name];new.append((name,list(values),body))
for name,values,body in records:
    if (name in ['lib','lib64','sbin'] or name.startswith(('lib/','lib64/','sbin/'))) and '/modules' not in name:
        new.append((name,list(values),body))
def add(name,body,mode):
    assert name not in [n for n,_,_ in new],name
    new.append((name,[100+len(new),mode,0,0,1,0,len(body),0,0,0,0,0,0],body))
def directory(name):
    for p in reversed(Path(name).parents):
        s=p.as_posix()
        if s!='.' and s not in [n for n,_,_ in new]:add(s,b'',stat.S_IFDIR|0o755)
    if name not in [n for n,_,_ in new]:add(name,b'',stat.S_IFDIR|0o755)
add('bin/busybox',busybox,stat.S_IFREG|0o755)
for app in required:add('bin/'+app,b'busybox',stat.S_IFLNK|0o777)
modules=root/f'lib/modules/{release}'
staged=[]
for module in ['squashfs','overlay']:
    deps=subprocess.check_output(['modprobe','-d',str(root),'-S',release,'--show-depends',module],text=True)
    for line in deps.splitlines():
        if not line.startswith('insmod '):continue
        path=Path(line.split()[1]);assert path.resolve().is_relative_to(root.resolve())
        relative=path.relative_to(modules).as_posix()
        dest=f'lib/modules/{release}/'+relative
        if dest in staged:continue
        data=path.read_bytes();assert data[:4]==b'\x7fELF' and struct.unpack_from('<H',data,18)[0]==183
        directory(str(Path(dest).parent));add(dest,data,stat.S_IFREG|0o644);staged.append(dest)
for name in ['modules.dep','modules.alias','modules.softdep','modules.builtin','modules.order']:
    path=modules/name
    if path.exists():add(f'lib/modules/{release}/'+name,path.read_bytes(),stat.S_IFREG|0o644)
init=(P/'armbian/official-graphics/init.sh.in').read_text().replace('@OFFICIAL_ROOT_SHA256@',root_record['sha256']).encode()
assert b'@OFFICIAL_' not in init
add('init',init,stat.S_IFREG|0o755)
probe=(P/'armbian/official-graphics/gpu-probe.py').read_bytes()
compile(probe,'gpu-probe.py','exec')
add('f8-gpu-probe',probe,stat.S_IFREG|0o644)
wayland_helpers={}
for name in ['wayland-run','wayland-client']:
    data=(P/f'armbian/official-graphics/{name}.sh').read_bytes()
    add('f8-'+name,data,stat.S_IFREG|0o755)
    wayland_helpers[name]=hashlib.sha256(data).hexdigest()
    path=work/(name+'.sh');path.write_bytes(data)
    subprocess.run(['qemu-aarch64-static',str(work/'busybox'),'sh','-n',str(path)],check=True)
add('f8-evaluation-report',(P/'armbian/official-graphics/report.sh').read_bytes(),stat.S_IFREG|0o755)
fat=work/'logs.img'
with fat.open('wb') as stream:stream.truncate(16*1024*1024)
subprocess.run(['mkfs.vfat','-n','F8AG1',str(fat)],check=True,stdout=subprocess.DEVNULL)
subprocess.run(['fsck.vfat','-n',str(fat)],check=True,stdout=subprocess.DEVNULL)
add('f8-firstboot-logs.img',fat.read_bytes(),stat.S_IFREG|0o600)
for name,data in [('init',init),('report',(P/'armbian/official-graphics/report.sh').read_bytes())]:
    path=work/(name+'.sh');path.write_bytes(data)
    subprocess.run(['qemu-aarch64-static',str(work/'busybox'),'sh','-n',str(path)],check=True)
archive=helper.cpio_write(new);readback={n:b for n,_,b in helper.cpio_read(archive)}
assert readback['init']==init
assert not any('6.1.172' in n for n in readback)
(work/'ramdisk').write_bytes(gzip.compress(archive,compresslevel=6,mtime=0))
source_dt=BASE_OUT/'f8-official-graphics-r1.NOT-APPROVED.dtb'
(work/'fdt').write_bytes(source_dt.read_bytes())
dt=fdt(source_dt.read_bytes())
cmdline=dt['/chosen']['bootargs'].decode().rstrip('\0').replace('f8-evaluation.target','f8-official-graphics.target')
assert not any(arg.startswith('cma=') for arg in cmdline.split())
cmdline+=' cma=256M' # Preserve the selected official desktop image's extraargs.
subprocess.run(['fdtput','-t','s',str(work/'fdt'),'/chosen','bootargs',cmdline],check=True)
(work/'kernel').write_bytes(kernel.read_bytes())
(work/'resource').write_bytes((P/'vendor/ubuntu-5.10.160/boot-assets/resource.img').read_bytes())
its=re.search(r"    its = '''(.*?)'''",(P/'tools/build-usb-bootlog.py').read_text(),re.S)[1]
its=its.replace('F8-PRO read-only USB boot log diagnostic','F8-PRO official Armbian GPU/display NOT APPROVED')
(work/'boot.its').write_text(its)
image=O/'F8_OFFICIAL_ARMBIAN_GPU_G1_NOT_APPROVED.img'
listing=subprocess.check_output(['mkimage','-E','-p','0x800','-f','boot.its',str(image)],cwd=work,text=True)
(O/'mkimage.txt').write_text(listing)
blob=image.read_bytes();fit=fdt(blob)
for name in ['kernel','fdt','ramdisk','resource']:
    props=fit['/images/'+name];start=int.from_bytes(props['data-position'],'big');size=int.from_bytes(props['data-size'],'big')
    data=blob[start:start+size];assert data==(work/name).read_bytes()
    assert hashlib.sha256(data).digest()==fit['/images/'+name+'/hash']['value']
assert image.stat().st_size<64*1024*1024
memory=json.loads((P/'analysis/armbian/live-memory-baseline.json').read_text())
banks=[(int(x['base'],16),int(x['base'],16)+int(x['size'],16)) for x in memory['banks']]
ranges={'kernel':(0x400000,0x400000+runtime),'dtb':(0x8300000,0x8300000+(work/'fdt').stat().st_size+12288),
        'initrd':(0xa200000,0xa200000+(work/'ramdisk').stat().st_size)}
for name,(a,b) in ranges.items():assert any(x<=a<b<=y for x,y in banks),name
for name,(a,b) in ranges.items():
    for other,(x,y) in ranges.items():
        if name!=other:assert not (a<y and x<b)
backup=P/'outputs/armbian/firstboot-diagnostic/CURRENT-BOOT-ROLLBACK-64MiB.img'
assert hashlib.sha256(backup.read_bytes()).hexdigest()=='7e51e71f7ec7439357e5ea2fbb97118715fe5fcf10401b638609df33567b1dd1'
(O/'init-script.txt').write_bytes(init)
(O/'initramfs.cpio.gz').write_bytes((work/'ramdisk').read_bytes())
(O/'boot-graphics.NOT-APPROVED.dtb').write_bytes((work/'fdt').read_bytes())
report={'scope':'Official Armbian GPU/Wayland boot-only package, NOT ready to flash until root staging and review',
        'file':image.name,'bytes':image.stat().st_size,'sha256':hashlib.sha256(blob).hexdigest(),
        'official_kernel_sha256':hashlib.sha256(kernel.read_bytes()).hexdigest(),
        'kernel_runtime_bytes':runtime,'kernel_text_offset':offset,'rootfs_sha256':root_record['sha256'],
        'rootfs_remote_path':'/var/lib/f8-pro/armbian-official-26.8.1/rootfs.squashfs',
        'rootfs_staged':False,'log_volume':'F8AG1','matching_initramfs_modules':staged,
        'ram_gpu_probe_override_sha256':hashlib.sha256(probe).hexdigest(),
        'ram_report_override_sha256':hashlib.sha256((P/'armbian/official-graphics/report.sh').read_bytes()).hexdigest(),
        'ram_wayland_helpers_sha256':wayland_helpers,
        'official_desktop_cma_argument_preserved':'cma=256M',
        'fit_payload_hashes_verified':True,'arm64_shell_checks_passed':True,
        'layout_with_12k_dtb_pad_verified':True,'rollback_hash_verified':True,
        'hardware_test_performed':False,'ready_for_user_flash':False,
        'remaining':['Verify packed blkid and BusyBox module dependency parsing',
                     'Stage and readback-verify official root on restored Arch',
                     'Final package review and user-coordinated boot-only trial']}
(O/'boot-manifest.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
