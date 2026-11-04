"""Correct PWM14 backlight mux away from the factory motor GPIO; BOOT only."""
import copy,hashlib,json,struct,subprocess,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'tools'))
from inspect_images import fdt
base=P/'outputs/armbian/official-f8-native-audio-a1'
prior=json.loads((base/'preflight.json').read_text())
blob=(base/prior['file']).read_bytes();assert hashlib.sha256(blob).hexdigest()=='7ed3dab57aa6eb84ddc13e50b1d58104815962a5c18e7d7f09e46f876a76f2e7'
ownership=json.loads((P/'local/hardware/armbian-native-audio-a1-20261030-01/backlight-motor-ownership.json').read_text())
lines='\n'.join(s for group in ownership['pinmux'].values() for s in group)
assert 'pin 138 (gpio4-10): (MUX UNCLAIMED) (GPIO UNCLAIMED)' in lines
assert 'pin 114 (gpio3-18): febf0020.pwm' in lines
out=P/'outputs/armbian/official-f8-native-audio-a2';out.mkdir(exist_ok=True)
assert not (out/'preflight.json').exists()
work=Path('/var/tmp/f8-pro-armbian/native-audio-a2');work.mkdir(exist_ok=True)
fit=fdt(blob);original={}
for name in ['kernel','fdt','ramdisk','resource']:
    prop=fit['/images/'+name];a=int.from_bytes(prop['data-position'],'big');n=int.from_bytes(prop['data-size'],'big')
    body=blob[a:a+n];assert hashlib.sha256(body).digest()==fit['/images/'+name+'/hash']['value']
    original[name]=body;(work/name).write_bytes(body)
before=fdt(original['fdt']);factory=fdt((P/'vendor/ubuntu-5.10.160/boot-assets/board.dtb').read_bytes())
def refs(t):return {v['phandle']:k for k,v in t.items() if 'phandle' in v}
def pin(t,path):
    raw=t[path]['rockchip,pins'];assert len(raw)==16
    bank,n,func,_=struct.unpack('>4I',raw);cfg=t[refs(t)[raw[12:16]]]
    return [bank,n,func],{k:v.hex() for k,v in cfg.items() if k!='phandle'}
pwm='/pwm@febf0020';m0='/pinctrl/pwm14/pwm14m0-pins';m1='/pinctrl/pwm14/pwm14m1-pins'
assert refs(before)[before[pwm]['pinctrl-0']]==m0
assert pin(before,m0)[0]==[3,18,11]
assert refs(factory)[factory[pwm]['pinctrl-0']]==m1
factory_pin,factory_cfg=pin(factory,m1)
assert factory_pin==[4,10,11]
assert before['/backlight']['pwms'][4:]==factory['/backlight']['pwms'][4:]
def gpio(t,raw):return refs(t)[raw[:4]],raw[4:]
assert gpio(before,before['/backlight']['enable-gpios'])==gpio(factory,factory['/backlight']['enable-gpios'])
assert gpio(factory,factory['/vibrator']['vibrator-gpio'])[0].endswith('gpio@fec40000')
assert int.from_bytes(factory['/vibrator']['vibrator-gpio'][4:8],'big')==18
expected=copy.deepcopy(before);created=[]
if m1 not in before:
    cfgmatches=[(path,value) for path,value in before.items() if path.startswith('/pinctrl/') and 'phandle' in value and {k:v.hex() for k,v in value.items() if k!='phandle'}==factory_cfg]
    assert cfgmatches,'Need exact factory pinconf match'
    cfg=sorted(cfgmatches,key=lambda item:item[0])[0][1]['phandle']
    handle=max(int.from_bytes(v['phandle'],'big') for v in before.values() if 'phandle' in v)+1
    assert handle<0xfffffffe
    expected[m1]={'rockchip,pins':struct.pack('>3I',4,10,11)+cfg,'phandle':struct.pack('>I',handle)}
    subprocess.run(['fdtput','-c',str(work/'fdt'),m1],check=True)
    subprocess.run(['fdtput','-t','x',str(work/'fdt'),m1,'rockchip,pins','4','a','b',hex(int.from_bytes(cfg,'big'))],check=True)
    subprocess.run(['fdtput','-t','x',str(work/'fdt'),m1,'phandle',hex(handle)],check=True)
    created.append(m1)
assert pin(expected,m1)==pin(factory,m1)
expected[pwm]['pinctrl-0']=expected[m1]['phandle']
subprocess.run(['fdtput','-t','x',str(work/'fdt'),pwm,'pinctrl-0',hex(int.from_bytes(expected[m1]['phandle'],'big'))],check=True)
assert fdt((work/'fdt').read_bytes())==expected,'Only PWM14 pinctrl may change'
assert len((work/'fdt').read_bytes())<len(original['fdt'])+4096
memory=json.loads((P/'analysis/armbian/live-memory-baseline.json').read_text())
assert any(int(b['base'],16)<=0x8300000 and 0x8300000+len((work/'fdt').read_bytes())+12288<=int(b['base'],16)+int(b['size'],16) for b in memory['banks'])
(work/'boot.its').write_bytes(Path('/var/tmp/f8-pro-armbian/native-audio-a1/boot.its').read_bytes())
target=out/'BOOT_ONLY_ARMBIAN_NATIVE_AUDIO_A2.img'
subprocess.run(['mkimage','-E','-p','0x800','-f','boot.its',str(target)],cwd=work,check=True,stdout=subprocess.DEVNULL)
data=target.read_bytes();tree=fdt(data)
for name in ['kernel','fdt','ramdisk','resource']:
    prop=tree['/images/'+name];a=int.from_bytes(prop['data-position'],'big');n=int.from_bytes(prop['data-size'],'big');value=data[a:a+n]
    assert value==(work/name).read_bytes() and hashlib.sha256(value).digest()==tree['/images/'+name+'/hash']['value']
    if name!='fdt':assert value==original[name]
assert len(data)<64*1024**2
record={'file':target.name,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'boot_lba':'0x00008000',
 'rootfs_reflash_required':False,'dt_changed_properties':[[pwm,'pinctrl-0']],'dt_added_nodes':created,
 'old_pin':'GPIO3_C2 PWM14_M0 (factory vibrator GPIO)','new_pin':'GPIO4_B2 PWM14_M1 (factory backlight)',
 'factory_pin_config_exact_match':True,'new_pin_unclaimed_on_target':True,'backlight_period_and_enable_gpio_unchanged':True,
 'kernel_ramdisk_resource_unchanged':True,'fdt_growth_bank_checked':True,'fit_hashes_verified':True,
 'battery_configuration_unchanged':True,'cold_boot_verified':False,'motor_stopped_user_confirmed':False,
 'audio_playback_verified':False,'includes_audio_a1':True}
(out/'preflight.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record,indent=2),flush=True)
