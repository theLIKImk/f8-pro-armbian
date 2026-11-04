"""Wire the existing USB2 PHY orientation/BVALID provider, retaining U3 role graph."""
import copy,hashlib,json,subprocess,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'tools'))
from inspect_images import fdt
from f8_resource_image import parse,replace_dtb
base=P/'outputs/armbian/official-f8-native-usb-u3';prior=json.loads((base/'preflight.json').read_text())
e=P/'local/hardware/armbian-native-usb-20261101'
identity=json.loads((e/'u3/identity.json').read_text());load=json.loads((e/'u3/module-load01.json').read_text())
flash=json.loads((e/'u3flash01.json').read_text());phy=json.loads((e/'u3/phy01.json').read_text())
assert load['module_loaded'] and load['insmod']['exit']==0
assert '[host]' in flash['typec']['port0']['data_role'] and phy['dwc3_mode'].strip()=='host'
assert len(flash['usb_devices'])==2 and all(k.startswith('usb') for k in flash['usb_devices'])
reference=json.loads((P/'analysis/armbian/usb2-orientation-20261101/audit.json').read_text())
assert any('rk3588s-tablet-rk806-single.dtsi' in k and '&u2phy0' in v for k,v in reference['usb2phy_orientation_examples'].items())
actual=json.loads((P/'analysis/armbian/official-usb-phy-20261101/report.json').read_text())
assert 'rockchip_usb2phy_orien_sw_set' in actual
blob=(base/prior['file']).read_bytes();assert hashlib.sha256(blob).hexdigest()==prior['sha256']
out=P/'outputs/armbian/official-f8-native-usb-u4';out.mkdir(exist_ok=True);assert not (out/'preflight.json').exists()
work=Path('/var/tmp/f8-pro-armbian/native-usb-u4');work.mkdir(exist_ok=True)
fit=fdt(blob);original={}
for name in ['kernel','fdt','ramdisk','resource']:
    v=fit['/images/'+name];a=int.from_bytes(v['data-position'],'big');n=int.from_bytes(v['data-size'],'big')
    original[name]=blob[a:a+n];assert hashlib.sha256(original[name]).digest()==fit['/images/'+name+'/hash']['value']
    (work/name).write_bytes(original[name])
assert parse(original['resource'])['rk-kernel.dtb']==original['fdt']
before=fdt(original['fdt']);expected=copy.deepcopy(before)
handle=max(int.from_bytes(v['phandle'],'big') for v in before.values() if 'phandle' in v)+1
def cell(n):return n.to_bytes(4,'big')
def node(path):
    if path in expected:return
    node(path.rsplit('/',1)[0] or '/')
    subprocess.run(['fdtput','-c',str(work/'fdt'),path],check=True);expected[path]={}
def prop(path,key,value):
    node(path);subprocess.run(['fdtput','-t','bx',str(work/'fdt'),path,key,*[f'{b:02x}' for b in value]],check=True)
    expected[path][key]=value
parent='/syscon@fd5d0000/usb2-phy@0';otg=parent+'/otg-port'
connector='/i2c@fec80000/fusb302@22/connector'
phyep=parent+'/port/endpoint';peerep=connector+'/ports/port@0/endpoint'
assert 'orientation-switch' not in before[parent] and 'rockchip,typec-vbus-det' not in before[otg]
factory=fdt((P/'vendor/ubuntu-5.10.160/boot-assets/board.dtb').read_bytes())
assert factory[otg]['rockchip,typec-vbus-det']==b''
prop(parent,'orientation-switch',b'');prop(otg,'rockchip,typec-vbus-det',b'')
prop(connector+'/ports','#address-cells',cell(1));prop(connector+'/ports','#size-cells',cell(0))
prop(connector+'/ports/port@0','reg',cell(0))
prop(phyep,'phandle',cell(handle));prop(peerep,'phandle',cell(handle+1))
prop(phyep,'remote-endpoint',cell(handle+1));prop(peerep,'remote-endpoint',cell(handle))
prop('/chosen','f8-usb-trial',b'u4\0')
dt=(work/'fdt').read_bytes();assert fdt(dt)==expected
tcpc='/i2c@fec80000/fusb302@22/port/endpoint';controller='/usbdrd3_0/usb@fc000000/port/endpoint'
assert expected[tcpc]==before[tcpc] and expected[controller]==before[controller]
handles=[v['phandle'] for v in expected.values() if 'phandle' in v];assert len(handles)==len(set(handles))
assert len(dt)<len(original['fdt'])+4096
(work/'resource').write_bytes(replace_dtb(original['resource'],dt))
(work/'boot.its').write_bytes(Path('/var/tmp/f8-pro-armbian/native-usb-u3/boot.its').read_bytes())
target=out/'BOOT_ONLY_ARMBIAN_NATIVE_USB_U4.img'
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
report={'file':target.name,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'boot_lba':'0x00008000','rootfs_reflash_required':False,'base':'U3 cold desktop and automatic host controller role verified','usb2_phy_orientation_provider_enabled':True,'factory_typec_vbus_detect_restored':True,'reference_tablet_orientation_binding_checked':True,'actual_kernel_orientation_callback_present':True,'u3_tcpm_role_graph_unchanged':True,'fit_fdt_matches_resource_dtb':parse((work/'resource').read_bytes())['rk-kernel.dtb']==dt,'kernel_ramdisk_module_unchanged':True,'charger_pins_limits_pd_audio_backlight_unchanged':True,'module_staged_only':True,'module_path':'/usr/libexec/f8-pro/f8_otg_vbus_u2.ko','power_sampler_condition_skip_preserved':True,'fit_and_memory_verified':True,'cold_boot_verified':False,'usb_flash_enumeration_verified':False,'rollback_file':str(base/prior['file'])}
(out/'preflight.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2),flush=True)
