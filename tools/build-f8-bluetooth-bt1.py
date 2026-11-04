"""Build a Bluetooth-only DT extension of the verified U5 BOOT."""
import copy,hashlib,json,subprocess,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'tools'))
from inspect_images import fdt
from f8_resource_image import parse,replace_dtb
base=P/'outputs/armbian/official-f8-native-usb-u5'
blob=(base/'BOOT_ONLY_ARMBIAN_NATIVE_USB_U5.img').read_bytes()
assert hashlib.sha256(blob).hexdigest()=='9044ece30ff5806f975f9030b49dab8f8bed38226bce9385381dee5708c5e237'
out=P/'outputs/armbian/official-f8-bluetooth-bt1';out.mkdir(exist_ok=True)
assert not (out/'preflight.json').exists(),'Do not overwrite completed candidate'
work=Path('/var/tmp/f8-pro-armbian/bluetooth-bt1');work.mkdir(exist_ok=True)
tree=fdt(blob);original={}
for name in ['kernel','fdt','ramdisk','resource']:
    v=tree['/images/'+name];a=int.from_bytes(v['data-position'],'big');n=int.from_bytes(v['data-size'],'big')
    data=blob[a:a+n];assert hashlib.sha256(data).digest()==tree['/images/'+name+'/hash']['value']
    original[name]=data;(work/name).write_bytes(data)
before=fdt(original['fdt']);expected=copy.deepcopy(before)
uart=before['/aliases']['serial9'].rstrip(b'\0').decode()
assert uart=='/serial@febc0000'
rtc='/i2c@fec80000/hym8563@51';bt='/wireless-bluetooth'
def cells(raw):return [int.from_bytes(raw[i:i+4],'big') for i in range(0,len(raw),4)]
def resolve(raw):return next(p for p,v in before.items() if v.get('phandle')==raw)
assert [resolve(before[uart]['pinctrl-0'][i:i+4]) for i in (0,4)]==['/pinctrl/uart9/uart9m2-xfer','/pinctrl/uart9/uart9m2-ctsn']
assert cells(before['/pinctrl/uart9/uart9m2-xfer']['rockchip,pins'])[:3]==[3,28,10]
assert resolve(before[bt]['clocks'])==rtc
assert before[rtc]['clock-frequency']==(32768).to_bytes(4,'big')
for prop,bank,pin in [('BT,reset_gpio',0,28),('BT,wake_gpio',0,22),('BT,wake_host_irq',0,21),('uart_rts_gpios',3,26)]:
    value=cells(before[bt][prop]);assert value[1]==pin
    gpio=resolve(before[bt][prop][:4]);assert gpio==f'/pinctrl/gpio@{["fd8a0000","fec20000","fec30000","fec40000"][bank]}'
for path in [uart,rtc,bt]:
    assert before[path]['status']==b'disabled\0'
    subprocess.run(['fdtput','-t','s',str(work/'fdt'),path,'status','okay'],check=True)
    expected[path]['status']=b'okay\0'
# Explicitly request the board's known 32kHz external clock through CCF.
for prop,value in [('assigned-clocks',before[rtc]['phandle']),('assigned-clock-rates',(32768).to_bytes(4,'big'))]:
    assert prop not in before[rtc]
    subprocess.run(['fdtput','-t','bx',str(work/'fdt'),rtc,prop,*[f'{x:02x}' for x in value]],check=True)
    expected[rtc][prop]=value
subprocess.run(['fdtput','-t','s',str(work/'fdt'),'/chosen','f8-bluetooth-trial','bt1'],check=True)
expected['/chosen']['f8-bluetooth-trial']=b'bt1\0'
dt=(work/'fdt').read_bytes();assert fdt(dt)==expected
assert expected['/chosen']['bootargs']==before['/chosen']['bootargs']
assert expected['/chosen']['f8-usb-trial']==b'u5\0'
assert parse(original['resource'])['rk-kernel.dtb']==original['fdt']
(work/'resource').write_bytes(replace_dtb(original['resource'],dt))
(work/'boot.its').write_bytes(Path('/var/tmp/f8-pro-armbian/native-usb-u5/boot.its').read_bytes())
target=out/'BOOT_ONLY_ARMBIAN_BLUETOOTH_BT1.img'
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
 'base':'verified USB U5','enabled_nodes':[uart,rtc,bt],'external_clock_hz':32768,
 'fit_resource_dtb_synchronized':True,'limited_dt_diff_verified':True,'fit_hashes_and_memory_verified':True,
 'kernel_ramdisk_unchanged':True,'usb_profile_u5_preserved':True,'cmdline_unchanged':True,
 'rootfs_reflash_required':False,'cold_boot_verified':False,'controller_verified':False,'pairing_verified':False,
 'rollback_file':str(base/'BOOT_ONLY_ARMBIAN_NATIVE_USB_U5.img')}
(out/'preflight.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
