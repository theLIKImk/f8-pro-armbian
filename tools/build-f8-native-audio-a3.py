"""Route the codec MCLK through the existing external-IO clock provider."""
import copy,hashlib,json,re,struct,subprocess,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'tools'))
from inspect_images import fdt
base=P/'outputs/armbian/official-f8-native-audio-a2';prior=json.loads((base/'preflight.json').read_text())
assert prior['cold_boot_verified'] and prior['runtime_pwm_pin_verified']
evidence=json.loads((P/'local/hardware/armbian-native-audio-a2-20261030-01/silent-clock-01.json').read_text())
assert evidence['aplay']['exit']==0 and 'S16_LE' in evidence['hw_params'] and '48000' in evidence['hw_params']
gate=next(s for s in evidence['i2s_clocks'] if 'i2s0_mclkout_to_io' in s)
assert re.search(r'i2s0_mclkout_to_io\s+0\s+0',gate)
blob=(base/prior['file']).read_bytes();assert hashlib.sha256(blob).hexdigest()==prior['sha256']
out=P/'outputs/armbian/official-f8-native-audio-a3';out.mkdir(exist_ok=True)
assert not (out/'preflight.json').exists()
work=Path('/var/tmp/f8-pro-armbian/native-audio-a3');work.mkdir(exist_ok=True)
tree=fdt(blob);original={}
for name in ['kernel','fdt','ramdisk','resource']:
    prop=tree['/images/'+name];a=int.from_bytes(prop['data-position'],'big');n=int.from_bytes(prop['data-size'],'big')
    body=blob[a:a+n];assert hashlib.sha256(body).digest()==tree['/images/'+name+'/hash']['value']
    original[name]=body;(work/name).write_bytes(body)
before=fdt(original['fdt']);expected=copy.deepcopy(before)
codec='/i2c@fec90000/es8388@11';provider='/clocks/mclkout-i2s0@fd58c318'
assert before[provider]['compatible']==b'rockchip,clk-out\0'
assert before[provider]['#clock-cells']==b'\0'*4
assert before[provider]['clocks']==before[codec]['clocks']
assert before[provider]['clock-output-names']==b'i2s0_mclkout_to_io\0'
assert 'rockchip,bit-set-to-disable' in before[provider]
added=[]
if 'phandle' not in before[provider]:
    handle=max(int.from_bytes(v['phandle'],'big') for v in before.values() if 'phandle' in v)+1
    assert handle<0xfffffffe
    expected[provider]['phandle']=struct.pack('>I',handle)
    subprocess.run(['fdtput','-t','x',str(work/'fdt'),provider,'phandle',hex(handle)],check=True)
    added.append([provider,'phandle'])
handle=int.from_bytes(expected[provider]['phandle'],'big')
expected[codec]['clocks']=expected[provider]['phandle']
subprocess.run(['fdtput','-t','x',str(work/'fdt'),codec,'clocks',hex(handle)],check=True)
assert fdt((work/'fdt').read_bytes())==expected,'Only codec clock reference and provider handle may change'
assert expected[codec]['assigned-clocks']==before[codec]['assigned-clocks']
assert expected[codec]['assigned-clock-rates']==before[codec]['assigned-clock-rates']
assert len((work/'fdt').read_bytes())<len(original['fdt'])+4096
memory=json.loads((P/'analysis/armbian/live-memory-baseline.json').read_text())
assert any(int(b['base'],16)<=0x8300000 and 0x8300000+len((work/'fdt').read_bytes())+12288<=int(b['base'],16)+int(b['size'],16) for b in memory['banks'])
(work/'boot.its').write_bytes(Path('/var/tmp/f8-pro-armbian/native-audio-a2/boot.its').read_bytes())
target=out/'BOOT_ONLY_ARMBIAN_NATIVE_AUDIO_A3.img'
subprocess.run(['mkimage','-E','-p','0x800','-f','boot.its',str(target)],cwd=work,check=True,stdout=subprocess.DEVNULL)
data=target.read_bytes();fit=fdt(data)
for name in ['kernel','fdt','ramdisk','resource']:
    prop=fit['/images/'+name];a=int.from_bytes(prop['data-position'],'big');n=int.from_bytes(prop['data-size'],'big');value=data[a:a+n]
    assert value==(work/name).read_bytes() and hashlib.sha256(value).digest()==fit['/images/'+name+'/hash']['value']
    if name!='fdt':assert value==original[name]
assert len(data)<64*1024**2
record={'file':target.name,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'boot_lba':'0x00008000',
 'dt_changed_properties':[[codec,'clocks']], 'dt_added_properties':added,
 'internal_mclk_rate_and_assignment_unchanged':True,'codec_mclk_uses_existing_io_gate':True,
 'backlight_a2_fix_preserved':True,'kernel_ramdisk_resource_unchanged':True,'battery_configuration_unchanged':True,
 'rootfs_reflash_required':False,'fit_and_fdt_bank_verified':True,'cold_boot_verified':False,
 'physical_mclk_output_verified':False,'audio_playback_verified':False,
 'rollback_file':str(base/prior['file'])}
(out/'preflight.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record,indent=2),flush=True)
