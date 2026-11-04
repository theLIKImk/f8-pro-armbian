"""C2 official Image + preserved async waits + early official sensor modules.

Offline only. No device access or native-root writes. C3 is never an input.
"""
import copy,gzip,hashlib,importlib.util,json,os,subprocess,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'tools'))
from inspect_images import fdt
from f8_resource_image import parse,replace_dtb
def sha(data):return hashlib.sha256(data).hexdigest()
source=P/'outputs/armbian/official-f8-camera-c2/BOOT_ONLY_ARMBIAN_CAMERA_C2.img'
blob=source.read_bytes()
assert sha(blob)=='41b1f3f84f23107ee0de68a567406fa797de5436b65de6ab554acc538bb7247f'
out=P/'outputs/armbian/official-f8-camera-c4';out.mkdir(exist_ok=True)
assert not (out/'preflight.json').exists(),'Do not overwrite a completed artifact'
work=Path('/var/tmp/f8-pro-armbian/camera-c4');work.mkdir(exist_ok=True)
fit=fdt(blob);original={}
for name in ['kernel','fdt','ramdisk','resource']:
    prop=fit['/images/'+name];a=int.from_bytes(prop['data-position'],'big');n=int.from_bytes(prop['data-size'],'big')
    body=blob[a:a+n];assert hashlib.sha256(body).digest()==fit['/images/'+name+'/hash']['value']
    original[name]=body;(work/name).write_bytes(body)
assert len(original['kernel'])==46561792
assert sha(original['kernel'])=='a67daf71caefef6b97a22ba708bbb302b239a4a9b4874cadd17a217ebd0c37b7'
assert b'Linux version 6.1.115-vendor-rk35xx' in original['kernel']
before=fdt(original['fdt']);expected=copy.deepcopy(before)
cmd=before['/chosen']['bootargs'].rstrip(b'\0').decode()
old='initcall_blacklist=rockchip_cpufreq_driver_init'
new=old+',rkcif_clr_unready_dev,rkisp_clr_unready_dev'
assert cmd.count(old)==1 and len([x for x in cmd.split() if x.startswith('initcall_blacklist=')])==1
assert 'cpufreq.off=1' in cmd and 'f8_usb_u1=1' in cmd
def put(name,value):
    subprocess.run(['fdtput','-t','bx',str(work/'fdt'),'/chosen',name,*[f'{n:02x}' for n in value]],check=True)
    expected['/chosen'][name]=value
put('bootargs',cmd.replace(old,new).encode()+b'\0')
put('f8-camera-async-trial',b'c4\0')
# C2 chosen marker deliberately retained for the existing guarded root service.
assert expected['/chosen']['f8-camera-trial']==b'c2\0'
dt=(work/'fdt').read_bytes();assert fdt(dt)==expected
assert parse(original['resource'])['rk-kernel.dtb']==original['fdt']
(work/'resource').write_bytes(replace_dtb(original['resource'],dt))
assert parse((work/'resource').read_bytes())['rk-kernel.dtb']==dt
spec=importlib.util.spec_from_file_location('cpio',P/'tools/build-usb-bootlog.py')
cpio=importlib.util.module_from_spec(spec);spec.loader.exec_module(cpio)
records=cpio.cpio_read(gzip.decompress(original['ramdisk']))
old_records={n:(v,b) for n,v,b in records};assert len(old_records)==len(records)
patch=(P/'armbian/camera/early-sensors-c4.sh').read_bytes().replace(b'\r\n',b'\n')
anchor=b'cd /mnt/root || fail chdir\n'
assert old_records['init'][1].count(anchor)==1
patched=old_records['init'][1].replace(anchor,patch+b'\n'+anchor)
updated=[]
for name,values,body in records:
    if name=='init':body=patched
    fields=list(values);fields[6]=len(body);updated.append((name,fields,body))
archive=cpio.cpio_write(updated);checked=cpio.cpio_read(archive)
assert len(checked)==len(records)
for (name,values,body),(old_name,old_values,old_body) in zip(checked,records):
    assert name==old_name
    if name!='init':assert values==old_values and body==old_body,name
    else:
        assert body.replace(patch+b'\n',b'',1)==old_body
        assert [v for i,v in enumerate(values) if i not in (6,11,12)]==[v for i,v in enumerate(old_values) if i not in (6,11,12)]
busy=work/'busybox';busy.write_bytes(old_records['bin/busybox'][1]);busy.chmod(0o755)
init=work/'init.sh';init.write_bytes(patched)
subprocess.run(['qemu-aarch64-static',str(busy),'sh','-n',str(init)],check=True)
applets=subprocess.check_output(['qemu-aarch64-static',str(busy),'--list'],text=True).split()
assert all(x in applets for x in ['timeout','chroot'])
(work/'ramdisk').write_bytes(gzip.compress(archive,compresslevel=6,mtime=0))
(work/'boot.its').write_bytes((P/'armbian/camera/boot-c4.its').read_bytes())
target=out/'BOOT_ONLY_ARMBIAN_CAMERA_C4.img'
subprocess.run(['mkimage','-E','-p','0x800','-f','boot.its',str(target)],cwd=work,check=True,stdout=subprocess.DEVNULL,
               env={**os.environ,'SOURCE_DATE_EPOCH':str(int.from_bytes(fit['/']['timestamp'],'big'))})
data=target.read_bytes();tree=fdt(data)
for name in original:
    v=tree['/images/'+name];a=int.from_bytes(v['data-position'],'big');n=int.from_bytes(v['data-size'],'big');body=data[a:a+n]
    assert body==(work/name).read_bytes() and hashlib.sha256(body).digest()==tree['/images/'+name+'/hash']['value']
    if name=='kernel':assert body==original[name]
for path,props in tree.items():
    old_props=fit[path]
    assert set(props)==set(old_props),(path,'FIT properties added or lost')
    for prop,value in props.items():
        if path.startswith('/images/') and prop in ['data-position','data-size','value']:continue
        assert value==old_props[prop],(path,prop)
assert set(tree)==set(fit)
memory=json.loads((P/'analysis/armbian/live-memory-baseline.json').read_text())
for name,address,slack in [('fdt',0x8300000,12288),('ramdisk',0xa200000,0)]:
    size=(work/name).stat().st_size+slack
    assert any(int(b['base'],16)<=address and address+size<=int(b['base'],16)+int(b['size'],16) for b in memory['banks'])
assert len(data)<64*1024**2
report={'file':target.name,'bytes':len(data),'sha256':sha(data),'boot_lba':'0x00008000',
 'base':'camera-c2','official_c2_kernel_byte_identical':True,'kernel_sha256':sha(original['kernel']),
 'dt_changes_only':['/chosen/bootargs','/chosen/f8-camera-async-trial'],
 'camera_resources_graph_mclk_unchanged':True,'camera_profile_c2_for_existing_service':True,
 'blacklisted_initcalls':['rockchip_cpufreq_driver_init','rkcif_clr_unready_dev','rkisp_clr_unready_dev'],
 'ramdisk_changes_only':['init: early bounded gc5035/ov8858 modprobe after mount moves, before systemd'],
 'rootfs_reflash_required':False,'native_root_files_modified':False,
 'packed_arm64_shell_syntax_and_applets_verified':True,'fit_resource_hash_memory_capacity_checked':True,
 'cold_boot_verified':False,'frame_capture_verified':False,
 'rollback_file':'outputs/armbian/official-f8-camera-c2/BOOT_ONLY_ARMBIAN_CAMERA_C2.img'}
(out/'preflight.json').write_text(json.dumps(report,indent=2)+'\n')
(out/'dt-change.json').write_text(json.dumps({'old_cmdline':cmd,'new_cmdline':cmd.replace(old,new)},indent=2)+'\n')
print(json.dumps(report,indent=2))
