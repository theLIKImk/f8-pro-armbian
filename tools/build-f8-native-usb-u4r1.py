"""Put the physical USB2 OTG child before graph children for the vendor driver."""
import copy,hashlib,json,subprocess,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'tools'))
from inspect_images import fdt
from f8_resource_image import parse,replace_dtb
base=P/'outputs/armbian/official-f8-native-usb-u4';prior=json.loads((base/'preflight.json').read_text())
load=json.loads((P/'local/hardware/armbian-native-usb-20261101/u4/module-load01.json').read_text())
assert load['module_loaded'] and load['bindings']['6-0022'] is None
assert 'cannot register tcpm port' in load['deferred']['stdout']
blob=(base/prior['file']).read_bytes();assert hashlib.sha256(blob).hexdigest()==prior['sha256']
out=P/'outputs/armbian/official-f8-native-usb-u4r1';out.mkdir(exist_ok=True);assert not (out/'preflight.json').exists()
work=Path('/var/tmp/f8-pro-armbian/native-usb-u4r1');work.mkdir(exist_ok=True)
fit=fdt(blob);original={}
for name in ['kernel','fdt','ramdisk','resource']:
    v=fit['/images/'+name];a=int.from_bytes(v['data-position'],'big');n=int.from_bytes(v['data-size'],'big')
    original[name]=blob[a:a+n];assert hashlib.sha256(original[name]).digest()==fit['/images/'+name+'/hash']['value']
    (work/name).write_bytes(original[name])
before=fdt(original['fdt']);expected=copy.deepcopy(before)
parent='/syscon@fd5d0000/usb2-phy@0';otg=parent+'/otg-port'
def children(tree,path):return [p for p in tree if p.rsplit('/',1)[0]==path]
oldorder=children(before,parent);assert oldorder==[parent+'/port',otg],oldorder
assert not any(p.startswith(otg+'/') for p in before)
# fdtput creates a child at the start: re-create only the physical OTG node.
props=before[otg].copy();subprocess.run(['fdtput','-r',str(work/'fdt'),otg],check=True)
subprocess.run(['fdtput','-c',str(work/'fdt'),otg],check=True)
for key,value in props.items():
    subprocess.run(['fdtput','-t','bx',str(work/'fdt'),otg,key,*[f'{b:02x}' for b in value]],check=True)
subprocess.run(['fdtput','-t','s',str(work/'fdt'),'/chosen','f8-usb-trial','u4r1'],check=True)
expected['/chosen']['f8-usb-trial']=b'u4r1\0'
dt=(work/'fdt').read_bytes();after=fdt(dt)
assert after==expected,'All properties except trial identity must remain equal'
assert children(after,parent)==[otg,parent+'/port']
assert after[otg]==before[otg]
# Model the driver's num_ports=1 loop: it increments even for an ignored child.
def instantiated(order,num_ports=1):
    return [p for i,p in enumerate(order) if i<num_ports and p.rsplit('/',1)[1] in ['otg-port','host-port']]
assert instantiated(oldorder)==[] and instantiated(children(after,parent))==[otg]
assert parse(original['resource'])['rk-kernel.dtb']==original['fdt']
(work/'resource').write_bytes(replace_dtb(original['resource'],dt))
(work/'boot.its').write_bytes(Path('/var/tmp/f8-pro-armbian/native-usb-u4/boot.its').read_bytes())
target=out/'BOOT_ONLY_ARMBIAN_NATIVE_USB_U4R1.img'
subprocess.run(['mkimage','-E','-p','0x800','-f','boot.its',str(target)],cwd=work,check=True,stdout=subprocess.DEVNULL)
data=target.read_bytes();tree=fdt(data)
for name in original:
    v=tree['/images/'+name];a=int.from_bytes(v['data-position'],'big');n=int.from_bytes(v['data-size'],'big');body=data[a:a+n]
    assert body==(work/name).read_bytes() and hashlib.sha256(body).digest()==tree['/images/'+name+'/hash']['value']
    if name in ['kernel','ramdisk']:assert body==original[name]
memory=json.loads((P/'analysis/armbian/live-memory-baseline.json').read_text())
for name,address,slack in [('fdt',0x8300000,12288),('ramdisk',0xa200000,0)]:
    size=(work/name).stat().st_size+slack
    assert any(int(b['base'],16)<=address and address+size<=int(b['base'],16)+int(b['size'],16) for b in memory['banks'])
assert len(data)<64*1024**2
report={'file':target.name,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'boot_lba':'0x00008000','rootfs_reflash_required':False,'usb2_phy_child_order_before':oldorder,'usb2_phy_child_order_after':children(after,parent),'num_ports_one_iteration_regression_checked':True,'otg_node_properties_and_handle_preserved':True,'all_dt_properties_except_trial_identity_equal_u4':True,'fit_fdt_matches_resource_dtb':parse((work/'resource').read_bytes())['rk-kernel.dtb']==dt,'kernel_ramdisk_module_unchanged':True,'module_staged_only':True,'power_sampler_condition_skip_preserved':True,'fit_and_memory_verified':True,'cold_boot_verified':False,'phy_instance_and_orientation_registration_verified':False,'usb_flash_enumeration_verified':False,'rollback_file':str(P/'outputs/armbian/official-f8-native-usb-u3/BOOT_ONLY_ARMBIAN_NATIVE_USB_U3.img')}
(out/'preflight.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2),flush=True)
