"""Audio-only DT candidate on the verified native desktop T1r2 baseline."""
import copy,hashlib,json,struct,subprocess,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'tools'))
from inspect_images import fdt
base=P/'outputs/armbian/official-f8-desktop-t1r2'
prior=json.loads((base/'preflight.json').read_text());assert prior['cold_boot_verified'] and prior['runtime_handoff_hash_verified']
blob=(base/prior['file']).read_bytes();assert hashlib.sha256(blob).hexdigest()==prior['sha256']
audit=json.loads((P/'analysis/armbian/audio-wiring-20261030.json').read_text())
assert audit['different_fields']==['cpu_pins']
out=P/'outputs/armbian/official-f8-native-audio-a1';out.mkdir(exist_ok=True)
assert not (out/'preflight.json').exists()
work=Path('/var/tmp/f8-pro-armbian/native-audio-a1');work.mkdir(exist_ok=True)
tree=fdt(blob);original={}
for name in ['kernel','fdt','ramdisk','resource']:
    prop=tree['/images/'+name];a=int.from_bytes(prop['data-position'],'big');n=int.from_bytes(prop['data-size'],'big')
    body=blob[a:a+n];assert hashlib.sha256(body).digest()==tree['/images/'+name+'/hash']['value']
    original[name]=body;(work/name).write_bytes(body)
before=fdt(original['fdt']);expected=copy.deepcopy(before)
refs={v['phandle']:k for k,v in before.items() if 'phandle' in v}
def pin_values(t,path):
    r={v['phandle']:k for k,v in t.items() if 'phandle' in v};result=[]
    data=t[path]['rockchip,pins']
    for i in range(0,len(data),16):
        bank,pin,func,conf=struct.unpack('>4I',data[i:i+16]);cfg=t[r[data[i+12:i+16]]]
        result.append({'bank':bank,'pin':pin,'function':func,'config':{k:v.hex() for k,v in cfg.items() if k not in ['phandle','name']}})
    return result
groups=[]
for pin in audit['factory']['cpu_pins']:
    matches=[path for path,value in before.items() if path.startswith('/pinctrl/') and 'phandle' in value and 'rockchip,pins' in value and pin_values(before,path)==[pin]]
    assert matches,('Missing exact factory I2S pin group',pin)
    chosen=sorted(matches,key=lambda path:(not ('i2s0' in path),path))[0];groups.append(chosen)
cpu=audit['factory']['cpu'];codec='/i2c@fec90000/es8388@11';sound='/es8388-sound'
assert [x['pin'] for x in audit['factory']['cpu_pins']]==[21,19,28,23]
assert not ({(x['bank'],x['pin']) for x in audit['factory']['cpu_pins']} & {(1,24),(1,25)})
handles=b''.join(before[path]['phandle'] for path in groups)
subprocess.run(['fdtput','-t','x',str(work/'fdt'),cpu,'pinctrl-0',*[hex(int.from_bytes(before[path]['phandle'],'big')) for path in groups]],check=True)
expected[cpu]['pinctrl-0']=handles
for node in [cpu,codec,sound]:
    assert before[node]['status']==b'disabled\0'
    subprocess.run(['fdtput','-t','s',str(work/'fdt'),node,'status','okay'],check=True)
    expected[node]['status']=b'okay\0'
after=fdt((work/'fdt').read_bytes());assert after==expected,'Only four audio properties may change'
assert [pin_values(after,path)[0] for path in groups]==audit['factory']['cpu_pins']
assert after['/i2c@fec80000/charger@6a']==before['/i2c@fec80000/charger@6a']
(work/'boot.its').write_bytes(Path('/var/tmp/f8-pro-armbian/desktop-t1r2/boot.its').read_bytes())
target=out/'BOOT_ONLY_ARMBIAN_NATIVE_AUDIO_A1.img'
subprocess.run(['mkimage','-E','-p','0x800','-f','boot.its',str(target)],cwd=work,check=True,stdout=subprocess.DEVNULL)
data=target.read_bytes();fit=fdt(data)
for name in ['kernel','fdt','ramdisk','resource']:
    prop=fit['/images/'+name];a=int.from_bytes(prop['data-position'],'big');n=int.from_bytes(prop['data-size'],'big');value=data[a:a+n]
    assert value==(work/name).read_bytes() and hashlib.sha256(value).digest()==fit['/images/'+name+'/hash']['value']
    if name!='fdt':assert value==original[name]
assert len(data)<64*1024**2
record={'file':target.name,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),
 'boot_lba':'0x00008000','base':'verified native desktop T1r2','rootfs_reflash_required':False,
 'kernel_ramdisk_resource_unchanged':True,'dt_changed_properties':[[cpu,'pinctrl-0'],*[ [node,'status'] for node in [cpu,codec,sound]]],
 'factory_i2s_groups':groups,'factory_pin_config_exact_match':True,'audio_i2c_pin_collision_removed':True,
 'battery_dt_and_settings_unchanged':True,'no_test_playback_or_userspace_mixer_writes':True,
 'cold_boot_verified':False,'audio_playback_verified':False,'fit_hashes_verified':True,
 'rollback_file':str(base/prior['file'])}
(out/'preflight.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record,indent=2),flush=True)
