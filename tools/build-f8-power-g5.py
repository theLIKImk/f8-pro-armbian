"""G4-based passive power diagnostics; no charger writes, no tablet deployment."""
import copy
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import subprocess
import sys
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'tools'))
from inspect_images import fdt
base=P/'outputs/armbian/official-f8-touch-g4'
out=P/'outputs/armbian/official-f8-power-g5';out.mkdir(exist_ok=True)
assert not (out/'preflight.json').exists(),'Preserve completed G5'
prior=json.loads((base/'preflight.json').read_text())
assert prior['touch_hardware_accepted'] and prior['hardware_fix_verified']
blob=(base/prior['candidate_file']).read_bytes()
assert hashlib.sha256(blob).hexdigest()==prior['candidate_sha256']
work=Path('/var/tmp/f8-pro-armbian/official-power-g5');work.mkdir(exist_ok=True)
fit=fdt(blob)
for name in ['kernel','fdt','ramdisk','resource']:
    prop=fit['/images/'+name];start=int.from_bytes(prop['data-position'],'big');size=int.from_bytes(prop['data-size'],'big')
    data=blob[start:start+size];assert hashlib.sha256(data).digest()==fit['/images/'+name+'/hash']['value']
    (work/name).write_bytes(data)
before=fdt((work/'fdt').read_bytes());factory=fdt((P/'vendor/ubuntu-5.10.160/boot-assets/board.dtb').read_bytes())
bus='/i2c@fec80000';group='/pinctrl/i2c6/i2c6m3-xfer'
refs={v['phandle']:k for k,v in factory.items() if 'phandle' in v}
oldrefs={v['phandle']:k for k,v in before.items() if 'phandle' in v}
factory_group=refs[factory[bus]['pinctrl-0']];assert factory_group==group
raw_factory=factory[group]['rockchip,pins'];assert len(raw_factory)==32
old_group=oldrefs[before[bus]['pinctrl-0']]
old_raw=before[old_group]['rockchip,pins']
assert group not in before and len(old_raw)==32
handle=struct.pack('>I',max(int.from_bytes(k,'big') for k in oldrefs)+1)
raw=b''.join(raw_factory[i:i+12]+old_raw[i+12:i+16] for i in [0,16])
assert sorted([struct.unpack_from('>III',raw,i) for i in [0,16]])==[(4,8,9),(4,9,9)]
for i in [0,16]:
    a=before[oldrefs[raw[i+12:i+16]]];b=factory[refs[raw_factory[i+12:i+16]]]
    assert {k:v for k,v in a.items() if k!='phandle'}=={k:v for k,v in b.items() if k!='phandle'}
def put(path,key,data):
    subprocess.run(['fdtput','-t','x',str(work/'fdt'),path,key,
                    *[format(v,'x') for v in struct.unpack('>'+str(len(data)//4)+'I',data)]],check=True)
subprocess.run(['fdtput','-c',str(work/'fdt'),group],check=True)
put(group,'phandle',handle);put(group,'rockchip,pins',raw);put(bus,'pinctrl-0',handle)
model=b'F8-PRO official Armbian G5 passive power diagnostics\0'
subprocess.run(['fdtput','-t','s',str(work/'fdt'),'/','model',model[:-1].decode()],check=True)
expected=copy.deepcopy(before);expected[group]={'phandle':handle,'rockchip,pins':raw}
expected[bus]['pinctrl-0']=handle;expected['/']['model']=model
after=fdt((work/'fdt').read_bytes());assert after==expected
assert after[bus]['status']==b'okay\0'
for node in ['charger@6a','cw2015@62']:
    assert after[bus+'/'+node]['status']==b'disabled\0'
profile=after[bus+'/cw2015@62']['cellwise,battery-profile']
assert len(profile)==64 and profile==factory[bus+'/cw2015@62']['cellwise,battery-profile']
spec=importlib.util.spec_from_file_location('cpio_helper',P/'tools/build-usb-bootlog.py')
helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
records=helper.cpio_read(gzip.decompress((work/'ramdisk').read_bytes()))
old={n:b for n,_,b in records}
fat=work/'logs.img'
with fat.open('wb') as stream:stream.truncate(16*1024*1024)
subprocess.run(['mkfs.vfat','-n','F8AG5',str(fat)],check=True,stdout=subprocess.DEVNULL)
subprocess.run(['fsck.vfat','-n',str(fat)],check=True,stdout=subprocess.DEVNULL)
new=[];changed=[]
for name,values,body in records:
    data=body
    if name in ['init','f8-evaluation-report']:
        data=data.replace(b'ARMBIAN-G4',b'ARMBIAN-G5').replace(b'F8PROAG4',b'F8PROAG5').replace(b'f8_official_armbian_g4',b'f8_official_armbian_g5')
    if name=='f8-evaluation-report':
        anchor=b'    cat /etc/armbian-release >"$disk/ARMBIAN.TXT" 2>&1\n';assert anchor in data
        data=data.replace(anchor,anchor+b'''    timeout -k 2 15 python3 -I /usr/libexec/f8-pro/power-readonly.py --output /run/f8/power-late.json >"$disk/POWERLOG.TXT" 2>&1
    echo "late_exit=$?" >>"$disk/POWERLOG.TXT"
    for entry in power-early.json:POWER0.JSON power-late.json:POWER1.JSON power-early.log:POWER0.TXT; do
        source=${entry%:*}; target=${entry#*:}
        [ ! -f "/run/f8/$source" ] || cp "/run/f8/$source" "$disk/$target"
    done
    { ls -l /sys/bus/i2c/devices/i2c-6/of_node /sys/bus/i2c/devices/6-006a/driver /sys/bus/i2c/devices/6-0062/driver; cat /sys/kernel/debug/gpio; } >"$disk/POWERBUS.TXT" 2>&1
''')
    elif name=='f8-g3-assets/graphics-run':
        data=data.replace(b'G3',b'G5')
        anchor=b'timeout -k 5 20 insmod';assert anchor in data
        data=data.replace(anchor,b'timeout -k 2 15 python3 -I /usr/libexec/f8-pro/power-readonly.py --output /run/f8/power-early.json >/run/f8/power-early.log 2>&1 &\n'+anchor)
    elif name=='f8-firstboot-logs.img':data=fat.read_bytes()
    if data!=body:changed.append(name)
    fields=list(values);fields[6]=len(data);new.append((name,fields,data))
assert sorted(changed)==['f8-evaluation-report','f8-firstboot-logs.img','f8-g3-assets/graphics-run','init']
script=(P/'armbian/official-graphics/power-readonly.py').read_bytes()
template=next(v for n,v,b in records if n=='f8-g3-assets/touch-events.py')
fields=list(template);fields[6]=len(script)
new.append(('f8-g3-assets/power-readonly.py',fields,script))
packed=helper.cpio_write(new);check={n:b for n,_,b in helper.cpio_read(packed)}
for name,_,body in records:
    if name not in changed:assert check[name]==body,name
assert hashlib.sha256(check['f8-g3-assets/f8_gsl_shuping.ko']).hexdigest()==prior['touch_module_sha256']
busybox=work/'busybox';busybox.write_bytes(check['bin/busybox']);busybox.chmod(0o755)
for name in ['init','f8-evaluation-report','f8-g3-assets/graphics-run']:
    path=work/(Path(name).name+'.sh');path.write_bytes(check[name])
    subprocess.run(['qemu-aarch64-static',str(busybox),'sh','-n',str(path)],check=True)
subprocess.run(['python3',str(P/'tools/test-f8-power-readonly.py')],check=True)
root=Path('/var/tmp/f8-pro-armbian/f8-official-armbian-26.8.1/rootfs')
assert 'CONFIG_I2C_CHARDEV=y' in (root/'boot/config-6.1.115-vendor-rk35xx').read_text()
probe=root/'tmp/f8-g5-power.py';result=root/'tmp/f8-g5-negative.json'
assert not probe.exists() and not result.exists()
try:
    probe.write_bytes(script)
    ret=subprocess.run(['chroot',str(root),'/usr/bin/python3','-I','/tmp/f8-g5-power.py','--output','/tmp/f8-g5-negative.json'],capture_output=True,text=True,timeout=25)
    negative=json.loads(result.read_text());assert ret.returncode==1 and 'error' in negative and not negative['complete']
finally:
    probe.unlink(missing_ok=True);result.unlink(missing_ok=True)
(work/'ramdisk').write_bytes(gzip.compress(packed,compresslevel=6,mtime=0))
its=Path('/var/tmp/f8-pro-armbian/official-touch-g4/boot.its').read_text().replace('G4 TOUCH','G5 PASSIVE POWER')
(work/'boot.its').write_text(its)
candidate=out/'BOOT_ONLY_ARMBIAN_26.8.1_POWER_G5_DIAGNOSTIC.img'
(out/'mkimage.txt').write_text(subprocess.check_output(['mkimage','-E','-p','0x800','-f','boot.its',str(candidate)],cwd=work,text=True))
data=candidate.read_bytes();tree=fdt(data);hashes={}
for name in ['kernel','fdt','ramdisk','resource']:
    props=tree['/images/'+name];a=int.from_bytes(props['data-position'],'big');size=int.from_bytes(props['data-size'],'big')
    value=data[a:a+size];assert value==(work/name).read_bytes()
    digest=hashlib.sha256(value).digest();assert digest==tree['/images/'+name+'/hash']['value'];hashes[name]=digest.hex()
assert len(data)<64*1024*1024
runtime=struct.unpack_from('<Q',(work/'kernel').read_bytes(),16)[0]
ranges={'kernel':(0x400000,0x400000+runtime),'dtb':(0x8300000,0x8300000+(work/'fdt').stat().st_size+12288),
        'initrd':(0xa200000,0xa200000+(work/'ramdisk').stat().st_size)}
mem=json.loads((P/'analysis/armbian/live-memory-baseline.json').read_text())
banks=[(int(x['base'],16),int(x['base'],16)+int(x['size'],16)) for x in mem['banks']]
for name,(a,b) in ranges.items():
    assert any(x<=a<b<=y for x,y in banks),name
    for other,(x,y) in ranges.items():
        if name!=other:assert not(a<y and x<b)
report={'scope':'G4 baseline plus passive BQ/CW diagnostics, not charging support',
 'candidate_file':candidate.name,'candidate_bytes':len(data),'candidate_sha256':hashlib.sha256(data).hexdigest(),
 'base_g4_sha256':prior['candidate_sha256'],'payload_sha256':hashes,'log_volume':'F8AG5',
 'i2c6_factory_pins_verified':True,'power_nodes_disabled':True,'touch_gpu_kernel_root_unchanged':True,
 'register_value_writes':0,'fault_latch_read_skipped':True,'no_bus_scan':True,
 'negative_arm64_probe':negative,'protocol_fixture_test_passed':True,
 'hardware_test_performed':False,'charging_supported':False,'deployment_performed':False,
 'expected_power_logs':['POWER0.JSON','POWER1.JSON','POWER0.TXT','POWERLOG.TXT','POWERBUS.TXT']}
(out/'preflight.json').write_text(json.dumps(report,indent=2)+'\n')
(out/'power-g5.dtb').write_bytes((work/'fdt').read_bytes())
print(json.dumps(report,indent=2))
