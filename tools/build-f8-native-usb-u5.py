"""Complete the reference tablet's USB2-only PIPE status selection."""
import copy,hashlib,json,subprocess,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'tools'))
from inspect_images import fdt
from f8_resource_image import parse,replace_dtb
base=P/'outputs/armbian/official-f8-native-usb-u4r1';prior=json.loads((base/'preflight.json').read_text())
assert prior['cold_boot_verified'] and prior['phy_instance_and_orientation_registration_verified']
audit=json.loads((P/'analysis/armbian/usb2-only-20261101.json').read_text())
assert audit['property_string_present_in_actual_official_kernel']
assert any('rk3588s-tablet-rk806-single.dtsi' in k and 'rockchip,sel-pipe-phystatus;' in v for k,v in audit['examples'].items())
reference=Path('/var/tmp/f8-pro-armbian/linux-rockchip-config/arch/arm64/boot/dts/rockchip/rk3588s-tablet-rk806-single.dtsi').read_text()
start=reference.index('&u2phy0 {');end=reference.index('&vdpu {',start)
context=reference[start:end]
for anchor in ['rockchip,sel-pipe-phystatus;', 'maximum-speed = "high-speed";', 'phys = <&u2phy0_otg>;', 'phy-names = "usb2-phy";', 'usb-role-switch;']:assert anchor in context
blob=(base/prior['file']).read_bytes();assert hashlib.sha256(blob).hexdigest()==prior['sha256']
out=P/'outputs/armbian/official-f8-native-usb-u5';out.mkdir(exist_ok=True);assert not (out/'preflight.json').exists()
(out/'reference-tablet-usb2-only.dtsi.txt').write_text(context)
work=Path('/var/tmp/f8-pro-armbian/native-usb-u5');work.mkdir(exist_ok=True)
fit=fdt(blob);original={}
for name in ['kernel','fdt','ramdisk','resource']:
    v=fit['/images/'+name];a=int.from_bytes(v['data-position'],'big');n=int.from_bytes(v['data-size'],'big')
    original[name]=blob[a:a+n];assert hashlib.sha256(original[name]).digest()==fit['/images/'+name+'/hash']['value']
    (work/name).write_bytes(original[name])
before=fdt(original['fdt']);expected=copy.deepcopy(before)
parent='/syscon@fd5d0000/usb2-phy@0';otg=parent+'/otg-port';usb='/usbdrd3_0/usb@fc000000'
assert [p for p in before if p.rsplit('/',1)[0]==parent]==[otg,parent+'/port']
assert before[usb]['maximum-speed']==b'high-speed\0' and before[usb]['phy-names']==b'usb2-phy\0'
assert 'rockchip,sel-pipe-phystatus' not in before[otg]
subprocess.run(['fdtput','-t','bx',str(work/'fdt'),otg,'rockchip,sel-pipe-phystatus'],check=True)
subprocess.run(['fdtput','-t','s',str(work/'fdt'),'/chosen','f8-usb-trial','u5'],check=True)
expected[otg]['rockchip,sel-pipe-phystatus']=b'';expected['/chosen']['f8-usb-trial']=b'u5\0'
dt=(work/'fdt').read_bytes();after=fdt(dt);assert after==expected
assert [p for p in after if p.rsplit('/',1)[0]==parent]==[otg,parent+'/port']
assert parse(original['resource'])['rk-kernel.dtb']==original['fdt']
(work/'resource').write_bytes(replace_dtb(original['resource'],dt))
(work/'boot.its').write_bytes(Path('/var/tmp/f8-pro-armbian/native-usb-u4r1/boot.its').read_bytes())
target=out/'BOOT_ONLY_ARMBIAN_NATIVE_USB_U5.img'
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
report={'file':target.name,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'boot_lba':'0x00008000','rootfs_reflash_required':False,'only_functional_dt_addition':[otg,'rockchip,sel-pipe-phystatus'],'reference_tablet_usb2_only_block_checked':True,'physical_phy_before_graph_child_verified':True,'fit_fdt_matches_resource_dtb':parse((work/'resource').read_bytes())['rk-kernel.dtb']==dt,'kernel_ramdisk_control_module_unchanged':True,'charger_configuration_unchanged':True,'module_staged_only':True,'module_path':'/usr/libexec/f8-pro/f8_otg_vbus_u2.ko','passive_diagnostic_addon_not_bundled':True,'power_sampler_condition_skip_preserved':True,'fit_and_memory_verified':True,'cold_boot_verified':False,'usb_flash_enumeration_verified':False,'rollback_file':str(base/prior['file'])}
(out/'preflight.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2),flush=True)
