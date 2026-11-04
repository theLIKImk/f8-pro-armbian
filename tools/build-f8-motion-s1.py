"""Correct factory I2C3 routing and expose one combined MPU6500 IIO device."""
import copy,hashlib,json,subprocess,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'tools'))
from inspect_images import fdt
from f8_resource_image import parse,replace_dtb
base=P/'outputs/armbian/official-f8-bluetooth-bt1';prior=json.loads((base/'preflight.json').read_text())
assert prior['cold_boot_verified'] and prior['controller_verified']
blob=(base/prior['file']).read_bytes();assert hashlib.sha256(blob).hexdigest()==prior['sha256']
out=P/'outputs/armbian/official-f8-motion-s1';out.mkdir(exist_ok=True)
assert not (out/'preflight.json').exists()
work=Path('/var/tmp/f8-pro-armbian/motion-s1');work.mkdir(exist_ok=True)
tree=fdt(blob);original={}
for name in ['kernel','fdt','ramdisk','resource']:
    v=tree['/images/'+name];a=int.from_bytes(v['data-position'],'big');n=int.from_bytes(v['data-size'],'big')
    original[name]=blob[a:a+n];assert hashlib.sha256(original[name]).digest()==tree['/images/'+name+'/hash']['value']
    (work/name).write_bytes(original[name])
before=fdt(original['fdt']);expected=copy.deepcopy(before)
vendor=fdt((P/'vendor/ubuntu-5.10.160/boot-assets/board.dtb').read_bytes())
def cell(n):return n.to_bytes(4,'big')
def cells(raw):return [int.from_bytes(raw[i:i+4],'big') for i in range(0,len(raw),4)]
def resolve(t,ph):return next(k for k,v in t.items() if v.get('phandle')==ph)
def prop(path,name,value):
    subprocess.run(['fdtput','-t','bx',str(work/'fdt'),path,name,*[f'{n:02x}' for n in value]],check=True)
    expected[path][name]=value
def create(path,values):
    subprocess.run(['fdtput','-c',str(work/'fdt'),path],check=True);expected[path]={}
    for name,value in values.items():prop(path,name,value)
bus='/i2c@feab0000';old=bus+'/mpu_acc@68';imu=bus+'/imu@68'
assert before[old]['status']==b'disabled\0' and before[bus+'/ak8963@f']['status']==b'disabled\0'
pins=cells(vendor[resolve(vendor,vendor[bus]['pinctrl-0'])]['rockchip,pins'])
assert pins[:3]==[3,15,9] and pins[4:7]==[3,16,9]
# Translate pin configuration by content, never copy foreign phandles.
for index in [3,7]:
    cfg=vendor[resolve(vendor,cell(pins[index]))].copy();cfg.pop('phandle',None)
    match=next(v['phandle'] for k,v in before.items() if k.startswith('/pinctrl/') and {a:b for a,b in v.items() if a!='phandle'}==cfg and 'phandle' in v)
    pins[index]=int.from_bytes(match,'big')
handle=max(int.from_bytes(v['phandle'],'big') for v in before.values() if 'phandle' in v)+1
create('/pinctrl/i2c3/f8-i2c3m1-xfer',{'rockchip,pins':b''.join(cell(n) for n in pins),'phandle':cell(handle)})
prop(bus,'pinctrl-0',cell(handle));prop(bus,'clock-frequency',vendor[bus]['clock-frequency'])
# Leave original unbound node disabled; no duplicate address is instantiated.
matrix=['0','1','0','1','0','0','0','0','-1'] # vendor sensor-dev layout 8
create(imu,{'compatible':b'invensense,mpu6500\0','reg':cell(0x68),'status':b'okay\0',
 'pinctrl-names':b'default\0','pinctrl-0':before[old]['pinctrl-0'],
 'mount-matrix':b''.join(s.encode()+b'\0' for s in matrix)})
# Phase S1 polls both axes; original irq_enable=0. Do not infer interrupt polarity.
prop('/chosen','f8-motion-trial',b's1\0')
dt=(work/'fdt').read_bytes();assert fdt(dt)==expected
assert expected['/chosen']['bootargs']==before['/chosen']['bootargs']
assert expected['/chosen']['f8-usb-trial']==b'u5\0' and expected['/chosen']['f8-bluetooth-trial']==b'bt1\0'
assert parse(original['resource'])['rk-kernel.dtb']==original['fdt']
(work/'resource').write_bytes(replace_dtb(original['resource'],dt))
(work/'boot.its').write_bytes(Path('/var/tmp/f8-pro-armbian/bluetooth-bt1/boot.its').read_bytes())
target=out/'BOOT_ONLY_ARMBIAN_MOTION_S1.img'
subprocess.run(['mkimage','-E','-p','0x800','-f','boot.its',str(target)],cwd=work,check=True,stdout=subprocess.DEVNULL)
data=target.read_bytes();tree=fdt(data)
for name in original:
    v=tree['/images/'+name];a=int.from_bytes(v['data-position'],'big');n=int.from_bytes(v['data-size'],'big');body=data[a:a+n]
    assert body==(work/name).read_bytes() and hashlib.sha256(body).digest()==tree['/images/'+name+'/hash']['value']
    if name in ['kernel','ramdisk']:assert body==original[name]
assert parse((work/'resource').read_bytes())['rk-kernel.dtb']==dt
memory=json.loads((P/'analysis/armbian/live-memory-baseline.json').read_text())
for name,address,slack in [('fdt',0x8300000,12288),('ramdisk',0xa200000,0)]:
    size=(work/name).stat().st_size+slack
    assert any(int(b['base'],16)<=address and address+size<=int(b['base'],16)+int(b['size'],16) for b in memory['banks'])
assert len(data)<64*1024**2
report={'file':target.name,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'boot_lba':'0x00008000',
 'base':'BT1 verified boot/controller/scan','i2c3_factory_pins':{'bank':3,'scl_sda_pins':[15,16],'function':9,'frequency':400000},
 'single_iio_device':imu,'legacy_nodes_disabled':True,'polling_no_irq':True,
 'mount_matrix_from_vendor_layout8':matrix,'mount_matrix_physical_verified':False,
 'no_unverified_sensor_supply_gpio_writes':True,'compass_enabled':False,
 'fit_resource_synchronized':True,'limited_dt_diff_fit_hashes_memory_verified':True,
 'kernel_ramdisk_cmdline_preserved':True,'bluetooth_usb_profiles_preserved':True,
 'cold_boot_verified':False,'accelerometer_verified':False,'gyroscope_verified':False,'autorotation_verified':False,
 'rootfs_reflash_required':False,'rollback_file':str(base/prior['file']),
 'dt_schema_note':'Polling stage intentionally omits interrupts required by upstream schema; no full schema validation claimed.'}
(out/'preflight.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
