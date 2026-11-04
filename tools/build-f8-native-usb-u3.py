"""Move USB role graph to the TCPM device node used by this vendor kernel."""
import copy,hashlib,json,subprocess,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'tools'))
from inspect_images import fdt
from f8_resource_image import parse,replace_dtb
base=P/'outputs/armbian/official-f8-native-usb-u2';prior=json.loads((base/'preflight.json').read_text())
e=P/'local/hardware/armbian-native-usb-20261101'
identity=json.loads((e/'u2/identity.json').read_text());load=json.loads((e/'u2/module-load01.json').read_text())
flash=json.loads((e/'u2flash01.json').read_text());path=json.loads((e/'u2/role-path01.json').read_text())
assert load['module_loaded'] and load['insmod']['exit']==0
assert '[host]' in flash['typec']['port0']['data_role']
assert path['usb_debug_files']['/sys/kernel/debug/usb/fc000000.usb/mode'].strip()=='device'
assert 'no port node found in /i2c@fec80000/fusb302@22' in flash['usb_log']['stdout']
blob=(base/prior['file']).read_bytes();assert hashlib.sha256(blob).hexdigest()==prior['sha256']
out=P/'outputs/armbian/official-f8-native-usb-u3';out.mkdir(exist_ok=True);assert not (out/'preflight.json').exists()
work=Path('/var/tmp/f8-pro-armbian/native-usb-u3');work.mkdir(exist_ok=True)
fit=fdt(blob);original={}
for name in ['kernel','fdt','ramdisk','resource']:
    v=fit['/images/'+name];a=int.from_bytes(v['data-position'],'big');n=int.from_bytes(v['data-size'],'big')
    original[name]=blob[a:a+n];assert hashlib.sha256(original[name]).digest()==fit['/images/'+name+'/hash']['value']
    (work/name).write_bytes(original[name])
assert parse(original['resource'])['rk-kernel.dtb']==original['fdt']
before=fdt(original['fdt']);expected=copy.deepcopy(before)
tcpc='/i2c@fec80000/fusb302@22';oldports=tcpc+'/connector/ports';old=oldports+'/port@0/endpoint'
newport=tcpc+'/port';new=newport+'/endpoint';usb='/usbdrd3_0/usb@fc000000/port/endpoint'
assert before[usb]['remote-endpoint']==before[old]['phandle']
assert before[old]['remote-endpoint']==before[usb]['phandle']
props=before[old].copy();assert set(props)=={'phandle','remote-endpoint'}
for p in list(expected):
    if p==oldports or p.startswith(oldports+'/'):del expected[p]
expected[newport]={};expected[new]=props
expected['/chosen']['f8-usb-trial']=b'u3\0'
subprocess.run(['fdtput','-r',str(work/'fdt'),oldports],check=True)
subprocess.run(['fdtput','-c',str(work/'fdt'),newport],check=True)
subprocess.run(['fdtput','-c',str(work/'fdt'),new],check=True)
for key,value in props.items():subprocess.run(['fdtput','-t','x',str(work/'fdt'),new,key,hex(int.from_bytes(value,'big'))],check=True)
subprocess.run(['fdtput','-t','s',str(work/'fdt'),'/chosen','f8-usb-trial','u3'],check=True)
dt=(work/'fdt').read_bytes();assert fdt(dt)==expected
# No other clocks, supplies, pins, GPIO or PD settings may change.
assert len(dt)<len(original['fdt'])+1024
handles=[v['phandle'] for v in expected.values() if 'phandle' in v];assert len(handles)==len(set(handles))
(work/'resource').write_bytes(replace_dtb(original['resource'],dt))
(work/'boot.its').write_bytes(Path('/var/tmp/f8-pro-armbian/native-usb-u2/boot.its').read_bytes())
target=out/'BOOT_ONLY_ARMBIAN_NATIVE_USB_U3.img'
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
report={'file':target.name,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'boot_lba':'0x00008000','rootfs_reflash_required':False,'base':'U2 cold desktop and module load verified','graph_endpoint_moved_from':old,'graph_endpoint_moved_to':new,'graph_handle_and_peer_preserved':True,'fit_fdt_matches_resource_dtb':parse((work/'resource').read_bytes())['rk-kernel.dtb']==dt,'kernel_ramdisk_module_unchanged':True,'charger_pins_limits_pd_audio_backlight_unchanged':True,'early_insmod_absent':True,'module_staged_only':True,'module_path':'/usr/libexec/f8-pro/f8_otg_vbus_u2.ko','power_sampler_condition_skip_preserved':True,'fit_and_memory_verified':True,'cold_boot_verified':False,'automatic_usb_role_switch_verified':False,'usb_flash_enumeration_verified':False,'rollback_file':str(base/prior['file'])}
(out/'preflight.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2),flush=True)
