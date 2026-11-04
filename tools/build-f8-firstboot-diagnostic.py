"""Build an isolated NOT-APPROVED first-kernel diagnostic FIT; never deploy."""
from collections import Counter
import argparse
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

P=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(P/'tools'))
from inspect_images import fdt
spec=importlib.util.spec_from_file_location('f8_usb_builder',P/'tools/build-usb-bootlog.py')
helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
cpio_read,cpio_write=helper.cpio_read,helper.cpio_write
B=Path('/var/tmp/f8-pro-armbian')
parser=argparse.ArgumentParser()
parser.add_argument('--revision',choices=['first','r2','r3','r4','r5'],default='first')
args=parser.parse_args()
is_r3=args.revision=='r3'
is_r5=args.revision=='r5'
is_r4=args.revision in ['r4','r5']
is_r2=args.revision in ['r2','r3','r4','r5']
suffix='' if args.revision=='first' else '-'+args.revision
source=B/'linux-rockchip-config'
work=B/('firstboot-diagnostic'+suffix)
out=P/'outputs/armbian'/('firstboot-diagnostic'+suffix)
work.mkdir(exist_ok=True);out.mkdir(parents=True,exist_ok=True)
assert not (out/'manifest.json').exists(),'Version already built; preserve its evidence and use a new revision'
def run(*args):return subprocess.check_output(args,text=True).strip()
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
assert run('git','-C',str(source),'rev-parse','HEAD')=='85233a85b67928000afc2e966bab86a8c414f1b4'
config=(B/'kernel-config-build/.config').read_text()
needed=['USB_DWC3','USB_DWC3_OF_SIMPLE','PHY_ROCKCHIP_INNO_USB2','USB_GADGET','USB_LIBCOMPOSITE',
        'USB_CONFIGFS','USB_CONFIGFS_MASS_STORAGE','USB_F_MASS_STORAGE','CONFIGFS_FS',
        'VFAT_FS','FAT_FS','NLS_CODEPAGE_437','NLS_ISO8859_1','BLK_DEV_LOOP','PSTORE_RAM']
for name in needed:assert f'CONFIG_{name}=y\n' in config,name
if is_r4:
    for name in ['SQUASHFS','OVERLAY_FS','CGROUPS','FHANDLE','INOTIFY_USER','UNIX','TMPFS']:
        assert f'CONFIG_{name}=y\n' in config,name
    staging=json.loads((P/'analysis/armbian/userspace/tablet-rootfs-staging.json').read_text())
    assert staging['sha256']=='a69fdacdc7ad5fc1d9239ffb271c40bb2e05fb151e0635c2f59b2ef70885a8dc'
bundle=json.loads((P/'outputs/armbian/evaluation-custom-set.json').read_text())
for role in ['kernel','initramfs']:
    item=next(x for x in bundle['artifacts'] if x['role']==role)
    assert digest(P/item['project_relative_path'])==item['sha256']
kernel=P/next(x for x in bundle['artifacts'] if x['role']=='kernel')['project_relative_path']
initramfs=P/next(x for x in bundle['artifacts'] if x['role']=='initramfs')['project_relative_path']
memory=json.loads((P/'analysis/armbian/live-memory-baseline.json').read_text())
cells=[]
for bank in memory['banks']:
    for field in ['base','size']:
        value=int(bank[field],16);cells.extend([value>>32,value&0xffffffff])
storage=memory['loader_fixed_vendor_storage']
reg=' '.join(hex(x) for x in cells)
draft=work/'firstboot.dts'
diagnostic_source='f8-pro-fifthboot-evaluation.dts' if is_r5 else 'f8-pro-fourthboot-evaluation.dts' if is_r4 else ('f8-pro-thirdboot-diagnostic.dts' if is_r3 else ('f8-pro-secondboot-diagnostic.dts' if is_r2 else 'f8-pro-firstboot-diagnostic.dts'))
draft.write_text('#include "'+diagnostic_source+'"\n/ { memory@200000 { device_type = "memory"; reg = <'+reg+'>; }; };\n'
    '&f8_vendor_storage_mem { reg = <0 '+storage['base']+' 0 '+storage['size']+'>; };\n')
includes=['-I',str(source/'include'),'-I',str(source/'arch/arm64/boot/dts/rockchip'),'-I',str(P/'armbian/dts')]
def compile_dt(path,stem):
    pre=subprocess.check_output(['cpp','-nostdinc','-undef','-D__DTS__','-x','assembler-with-cpp',*includes,str(path)])
    pp=work/(stem+'.pp.dts');pp.write_bytes(pre)
    output=work/(stem+'.dtb')
    r=subprocess.run(['dtc','-I','dts','-O','dtb','-o',str(output),str(pp)],capture_output=True,text=True)
    (out/(stem+'.dtc.log')).write_text(r.stderr);r.check_returncode()
    return output,Counter(re.findall(r'Warning \(([^)]+)\): ([^\n]+)',r.stderr))
_,base_warnings=compile_dt(P/'armbian/dts/f8-pro-compile-check.dts','base')
dtb,warnings=compile_dt(draft,'diagnostic')
assert not warnings-base_warnings,list((warnings-base_warnings).elements())
tree=fdt(dtb.read_bytes())
assert tree['/memory@200000']['reg']==b''.join(struct.pack('>I',x) for x in cells)
usb=tree['/usbdrd3_0/usb@fc000000']
assert usb['dr_mode']==b'peripheral\0' and usb['maximum-speed']==b'high-speed\0'
assert len(usb['phys'])==4 and usb['phy-names']==b'usb2-phy\0'
assert 'usb-role-switch' not in usb and 'quirk-skip-phy-init' not in usb
for path,properties in tree.items():
    compatible=properties.get('compatible',b'')
    if any(c in compatible for c in [b'gslX680_shuping',b'ti,bq25890',b'cellwise,cw2015',b'simple-panel-dsi']):
        assert properties.get('status')==b'disabled\0',path
phy=source/'drivers/phy/rockchip/phy-rockchip-inno-usb2.c'
(out/'phy-rockchip-inno-usb2.source.txt').write_bytes(phy.read_bytes())
if is_r2:
    cpufreq=(source/'drivers/cpufreq/rockchip-cpufreq.c').read_text()
    assert 'late_initcall(rockchip_cpufreq_driver_init)' in cpufreq
    (out/'rockchip-cpufreq.source.txt').write_text(cpufreq)
    symbols=run('aarch64-linux-gnu-nm','--defined-only',str(B/'kernel-config-build/vmlinux'))
    assert re.search(r'\bt\s+rockchip_cpufreq_driver_init$',symbols,re.M)
    assert 'CONFIG_KALLSYMS=y\n' in config
    assert 'initcall_blacklist' in (source/'init/main.c').read_text()
    node=tree['/i2c@fd880000']
    group=tree['/pinctrl/i2c0/i2c0m2-xfer']
    assert node['pinctrl-0']==group['phandle']
    assert tree['/display-subsystem']['status']==b'disabled\0'
    assert '/reserved-memory/drm-logo@00000000' not in tree
    if is_r3 or is_r4:
        uart=tree['/serial@feb50000']
        assert uart['status']==b'okay\0'
        assert uart['pinctrl-0']==tree['/pinctrl/uart2/uart2m0-xfer']['phandle']
records=cpio_read(gzip.decompress(initramfs.read_bytes()))
by_name={name:(values,body) for name,values,body in records}
busybox=by_name['bin/busybox'][1]
(work/'busybox').write_bytes(busybox);(work/'busybox').chmod(0o755)
apps=set(run('qemu-aarch64-static',str(work/'busybox'),'--list').splitlines())
required=['sh','mount','umount','mkdir','cat','sleep','uname','ls','dmesg','cp','sync','head','ln']
if is_r3 or is_r4:required+=['timeout','chroot']
if is_r4:required+=['sha256sum','switch_root']
if is_r5:required+=['chmod']
assert set(required)<=apps
init=(P/'armbian/initramfs/firstboot-diagnostic-init.sh').read_bytes()
if is_r2:
    observations=(P/'armbian/initramfs/secondboot-observations.sh').read_bytes()
    anchor=b'dmesg >/run/logdisk/DMESG.TXT'
    assert init.count(anchor)==1
    init=init.replace(anchor,observations+b'\n'+anchor)
    init=init.replace(b'F8PRO61FIRSTBOOT',b'F8PRO61R2').replace(b'6.1 firstboot RAM logs',b'6.1 R2 regulator logs')
if is_r3:
    anchor=b'dmesg >/run/logdisk/DMESG.TXT'
    init=init.replace(anchor,(P/'armbian/initramfs/thirdboot-observations.sh').read_bytes()+b'\n'+anchor)
    init=init.replace(b'F8PRO61R2',b'F8PRO61R3').replace(b'6.1 R2 regulator logs',b'6.1 R3 SMP userspace logs')
if is_r4:
    init=(P/('armbian/initramfs/fifthboot-evaluation-init.sh' if is_r5 else 'armbian/initramfs/fourthboot-evaluation-init.sh')).read_bytes()
(out/'init-script.txt').write_bytes(init)
subprocess.run(['qemu-aarch64-static',str(work/'busybox'),'sh','-n',str(out/'init-script.txt')],check=True)
fat=work/'logs.img'
with fat.open('wb') as stream:stream.truncate(16*1024*1024)
volume='F861R5' if is_r5 else 'F861R4' if is_r4 else ('F861R3' if is_r3 else ('F861R2' if is_r2 else 'F861LOGS'))
run('mkfs.vfat','-n',volume,str(fat))
subprocess.run(['fsck.vfat','-n',str(fat)],check=True,stdout=subprocess.DEVNULL)
new=[]
for name in ['dev','proc','sys','run','bin','dev/console','dev/null']:
    values,body=by_name[name];new.append((name,list(values),body))
if is_r3 or is_r4:
    for name,values,body in records:
        if name in ['lib','lib64','sbin'] or name.startswith(('lib/','lib64/','sbin/')):
            new.append((name,list(values),body))
    assert any(name=='sbin/blkid' for name,_,_ in new)
def add(name,body,mode):
    values=[100+len(new),mode,0,0,1,0,len(body),0,0,0,0,0,0]
    new.append((name,values,body))
add('bin/busybox',busybox,stat.S_IFREG|0o755)
for app in required:add('bin/'+app,b'busybox',stat.S_IFLNK|0o777)
add('init',init,stat.S_IFREG|0o755)
add('f8-firstboot-logs.img',fat.read_bytes(),stat.S_IFREG|0o600)
if is_r4:
    report_script=(P/('armbian/initramfs/fifthboot-evaluation-report.sh' if is_r5 else 'armbian/initramfs/evaluation-report.sh')).read_bytes()
    add('f8-evaluation-report',report_script,stat.S_IFREG|0o755)
    add('f8-eval-units',b'',stat.S_IFDIR|0o755)
    for path in sorted((P/'armbian/evaluation-units').iterdir()):
        add('f8-eval-units/'+path.name,path.read_bytes(),stat.S_IFREG|0o644)
    (out/'evaluation-report-script.txt').write_bytes(report_script)
    subprocess.run(['qemu-aarch64-static',str(work/'busybox'),'sh','-n',str(out/'evaluation-report-script.txt')],check=True)
archive=cpio_write(new)
checked={name:body for name,_,body in cpio_read(archive)}
assert checked['init']==init and checked['bin/busybox']==busybox
assert not any(name.endswith('.ko') or 'rootfs.squashfs' in name for name in checked)
ramdisk=work/'ramdisk';ramdisk.write_bytes(gzip.compress(archive,compresslevel=6,mtime=0))
for name,path in [('kernel',kernel),('fdt',dtb)]: (work/name).write_bytes(path.read_bytes())
(work/'resource').write_bytes((P/'vendor/ubuntu-5.10.160/boot-assets/resource.img').read_bytes())
# Reuse the established external-data FIT structure, not the original signature.
its_source=(P/'tools/build-usb-bootlog.py').read_text()
its=re.search(r"    its = '''(.*?)'''",its_source,re.S)[1]
its=its.replace('F8-PRO read-only USB boot log diagnostic','F8-PRO 6.1 diagnostic NOT APPROVED')
(work/'boot.its').write_text(its)
image=out/('F8-PRO-6.1-'+args.revision.upper()+'-NOT-APPROVED.img' if is_r2 else 'F8-PRO-6.1-FIRSTBOOT-NOT-APPROVED.img')
listing=subprocess.check_output(
    ['mkimage','-E','-p','0x800','-f','boot.its',str(image)],cwd=work,text=True)
(out/'mkimage.txt').write_text(listing)
assert image.stat().st_size<64*1024*1024
blob=image.read_bytes();fit=fdt(blob)
for name in ['kernel','fdt','ramdisk','resource']:
    props=fit['/images/'+name];offset=int.from_bytes(props['data-position'],'big');size=int.from_bytes(props['data-size'],'big')
    content=blob[offset:offset+size]
    assert content==(work/name).read_bytes()
    assert hashlib.sha256(content).digest()==fit['/images/'+name+'/hash']['value']
(out/'diagnostic.NOT-APPROVED.dtb').write_bytes(dtb.read_bytes())
(out/'initramfs-diagnostic.cpio.gz').write_bytes(ramdisk.read_bytes())
report={'scope':'Offline first-kernel diagnostic candidate; NOT APPROVED for deployment',
    'revision':args.revision,'log_volume_label':volume,
    'i2c0_mux_verified':is_r2,'vendor_cpufreq_initcall_blocked_by_cmdline_candidate':is_r2,
    'release':bundle['release'],'image_bytes':image.stat().st_size,'image_sha256':digest(image),
    'kernel_sha256':digest(kernel),'dtb_sha256':digest(dtb),'ramdisk_sha256':digest(ramdisk),
    'busybox_static_aarch64':struct.unpack_from('<H',busybox,18)[0]==183,
    'required_kernel_options_builtin':needed,'dt_unexpected_warnings':list((warnings-base_warnings).elements()),
    'fit_payloads_verified':True,'init_shell_syntax_verified':True,'ram_fat_fsck_passed':True,
    'memory_bank_source':'Old observed per-device banks; loader may rewrite',
    'reserved_vendor_storage_source':'Old observed per-device snapshot; loader may rewrite',
    'usb_mode':'USB2-only peripheral, fixed role','physical_partitions_mounted':False,
    'planned_root_probe':('Verified SquashFS + RAM overlay + basic systemd target' if is_r4 else ('Arch PARTUUID-checked ro,noload plus true/systemd --version' if is_r3 else 'none')),
    'planned_smp_bringup':is_r3 or is_r4,'planned_voltage_or_frequency_writes':False,
    'desktop_started':False,'hardware_test_performed':False,'deployment_approved':False,
    'pending':['Review USB2 forced-peripheral PHY behavior','Capture and verify CURRENT boot rollback backup',
               'Final padded layout check and first-test/restore instructions','User-coordinated boot-only test']}
(out/'manifest.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
