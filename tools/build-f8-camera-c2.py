"""Give the shared MCLK pin one owner and defer autofocus until capture works."""
import copy,hashlib,json,subprocess,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'tools'))
from inspect_images import fdt
from f8_resource_image import parse,replace_dtb
base=P/'outputs/armbian/official-f8-camera-c1';prior=json.loads((base/'preflight.json').read_text())
blob=(base/prior['file']).read_bytes();assert hashlib.sha256(blob).hexdigest()=='7a8d407f9aa32dee398e72f2a5539afd3f5d4fa276ca413e2e665ce9b8da4cc0'
out=P/'outputs/armbian/official-f8-camera-c2';out.mkdir(exist_ok=True);assert not (out/'preflight.json').exists()
work=Path('/var/tmp/f8-pro-armbian/camera-c2');work.mkdir(exist_ok=True)
tree=fdt(blob);original={}
for name in ['kernel','fdt','ramdisk','resource']:
    v=tree['/images/'+name];a=int.from_bytes(v['data-position'],'big');n=int.from_bytes(v['data-size'],'big')
    original[name]=blob[a:a+n];assert hashlib.sha256(original[name]).digest()==tree['/images/'+name+'/hash']['value'];(work/name).write_bytes(original[name])
before=fdt(original['fdt']);expected=copy.deepcopy(before)
def put(path,name,value):
    subprocess.run(['fdtput','-t','bx',str(work/'fdt'),path,name,*[f'{n:02x}' for n in value]],check=True);expected[path][name]=value
def remove(path,name):
    subprocess.run(['fdtput','-d',str(work/'fdt'),path,name],check=True);del expected[path][name]
front='/i2c@fead0000/gc5035@37';back='/i2c@fead0000/ov8858@36';power='/vcc-mipidcphy-regulator'
clock_pin=before[front]['pinctrl-0'];assert clock_pin==before[back]['pinctrl-0']
assert len(clock_pin)==4 and len(before[power]['pinctrl-0'])==4
put(power,'pinctrl-0',before[power]['pinctrl-0']+clock_pin)
for sensor in [front,back]:
    remove(sensor,'pinctrl-names');remove(sensor,'pinctrl-0')
put('/i2c@fead0000/dw9714@c','status',b'disabled\0');remove(back,'lens-focus')
put('/chosen','f8-camera-trial',b'c2\0')
dt=(work/'fdt').read_bytes();assert fdt(dt)==expected
for node in [front,back]:assert expected[node]['clocks']==before[node]['clocks'] and expected[node]['avdd-supply']==before[node]['avdd-supply']
assert expected['/chosen']['bootargs']==before['/chosen']['bootargs']
assert parse(original['resource'])['rk-kernel.dtb']==original['fdt']
(work/'resource').write_bytes(replace_dtb(original['resource'],dt));assert parse((work/'resource').read_bytes())['rk-kernel.dtb']==dt
(work/'boot.its').write_bytes(Path('/var/tmp/f8-pro-armbian/camera-c1/boot.its').read_bytes())
target=out/'BOOT_ONLY_ARMBIAN_CAMERA_C2.img'
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
report={'file':target.name,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'boot_lba':'0x00008000',
 'mclk_pin_single_owner':power,'both_sensor_clock_consumers_preserved':True,'autofocus_disabled_pending_camera_capture':True,
 'c1_media_graph_unchanged':True,'kernel_ramdisk_cmdline_unchanged':True,'fit_resource_hash_memory_capacity_checked':True,
 'native_root_camera_start_service_required':True,'never_hot_unbind_cif':True,'cold_boot_verified':False,
 'front_sensor_c2_verified':False,'back_sensor_verified':False,'frame_capture_verified':False,
 'rollback_file':str(P/'outputs/armbian/official-f8-motion-s1/BOOT_ONLY_ARMBIAN_MOTION_S1.img')}
(out/'preflight.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
