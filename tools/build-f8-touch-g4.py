"""Fix only I2C4 physical pinmux based on G3 timeout and factory pin evidence."""
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
base=P/'outputs/armbian/official-f8-touch-g3'
out=P/'outputs/armbian/official-f8-touch-g4';out.mkdir(exist_ok=True)
assert not (out/'preflight.json').exists(),'Preserve completed G4'
prior=json.loads((base/'preflight.json').read_text());source=base/prior['candidate_file']
blob=source.read_bytes();assert hashlib.sha256(blob).hexdigest()==prior['candidate_sha256']
work=Path('/var/tmp/f8-pro-armbian/official-touch-g4');work.mkdir(exist_ok=True)
fit=fdt(blob)
for name in ['kernel','fdt','ramdisk','resource']:
    props=fit['/images/'+name];offset=int.from_bytes(props['data-position'],'big');size=int.from_bytes(props['data-size'],'big')
    data=blob[offset:offset+size];assert hashlib.sha256(data).digest()==fit['/images/'+name+'/hash']['value']
    (work/name).write_bytes(data)
before=fdt((work/'fdt').read_bytes());factory=fdt((P/'vendor/ubuntu-5.10.160/boot-assets/board.dtb').read_bytes())
bus='/i2c@feac0000';group='/pinctrl/i2c4/i2c4m3-xfer'
refs={v['phandle']:k for k,v in factory.items() if 'phandle' in v}
factory_group=refs[factory[bus]['pinctrl-0']]
assert factory_group.endswith('i2c4m3-xfer')
original=factory[factory_group]['rockchip,pins']
old_refs={v['phandle']:k for k,v in before.items() if 'phandle' in v}
old_group=old_refs[before[bus]['pinctrl-0']]
old_raw=before[old_group]['rockchip,pins']
assert group not in before
handle=struct.pack('>I',max(int.from_bytes(h,'big') for h in old_refs)+1)
raw=b''.join(original[i:i+12]+old_raw[i+12:i+16] for i in range(0,len(original),16))
subprocess.run(['fdtput','-c',str(work/'fdt'),group],check=True)
subprocess.run(['fdtput','-t','x',str(work/'fdt'),group,'phandle',handle.hex()],check=True)
subprocess.run(['fdtput','-t','x',str(work/'fdt'),group,'rockchip,pins',
                *[format(v,'x') for v in struct.unpack('>'+str(len(raw)//4)+'I',raw)]],check=True)
for index in range(0,len(raw),16):assert raw[index:index+12]==original[index:index+12]
assert [struct.unpack_from('>III',raw,i) for i in range(0,len(raw),16)]==[(1,3,9),(1,2,9)]
subprocess.run(['fdtput','-t','x',str(work/'fdt'),bus,'pinctrl-0',format(int.from_bytes(handle,'big'),'x')],check=True)
subprocess.run(['fdtput','-t','s',str(work/'fdt'),'/','model','F8-PRO official Armbian G4 I2C4 m3 touch fix'],check=True)
after=fdt((work/'fdt').read_bytes());expected=copy.deepcopy(before)
expected[group]={'phandle':handle,'rockchip,pins':raw}
expected[bus]['pinctrl-0']=handle;expected['/']['model']=b'F8-PRO official Armbian G4 I2C4 m3 touch fix\0'
assert after==expected,'Do not change firmware, GPIO, voltage, timing or GPU configuration'
# Compare actual pin-config semantics too, not just bank/pin/function cells.
new_refs={v['phandle']:k for k,v in after.items() if 'phandle' in v}
for index in range(0,len(raw),16):
    a=after[new_refs[raw[index+12:index+16]]];b=factory[refs[original[index+12:index+16]]]
    assert {k:v for k,v in a.items() if k!='phandle'}=={k:v for k,v in b.items() if k!='phandle'}
spec=importlib.util.spec_from_file_location('cpio_helper',P/'tools/build-usb-bootlog.py')
helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
records=helper.cpio_read(gzip.decompress((work/'ramdisk').read_bytes()))
fat=work/'logs.img'
with fat.open('wb') as stream:stream.truncate(16*1024*1024)
subprocess.run(['mkfs.vfat','-n','F8AG4',str(fat)],check=True,stdout=subprocess.DEVNULL)
subprocess.run(['fsck.vfat','-n',str(fat)],check=True,stdout=subprocess.DEVNULL)
fat_data=fat.read_bytes();new=[];changed=[]
for name,values,body in records:
    data=body
    if name in ['init','f8-evaluation-report']:
        data=data.replace(b'ARMBIAN-G3',b'ARMBIAN-G4').replace(b'F8PROAG3',b'F8PROAG4').replace(b'f8_official_armbian_g3',b'f8_official_armbian_g4')
        if name=='f8-evaluation-report':
            anchor=b'    cat /proc/bus/input/devices >"$disk/INPUT.TXT"\n';assert anchor in data
            data=data.replace(anchor,anchor+b'''    timeout 10 journalctl -b _COMM=kwin_wayland --no-pager >"$disk/KWINAPP.TXT" 2>&1
    timeout 10 journalctl -b _UID=1600 --no-pager | grep -Ei 'OpenGL|EGL|renderer|Mesa|G610|llvmpipe|softpipe|libinput|touch' | head -n 250 >"$disk/USERGFX.TXT"
    { cat /sys/bus/i2c/devices/i2c-4/name; ls -l /sys/bus/i2c/devices/4-0040/driver; } >"$disk/I2CBUS.TXT" 2>&1
''')
    elif name=='f8-firstboot-logs.img':data=fat_data
    if data!=body:changed.append(name)
    fields=list(values);fields[6]=len(data);new.append((name,fields,data))
assert sorted(changed)==['f8-evaluation-report','f8-firstboot-logs.img','init']
check={n:b for n,_,b in helper.cpio_read(helper.cpio_write(new))}
for name,_,body in records:
    if name not in changed:assert check[name]==body,name
module=check['f8-g3-assets/f8_gsl_shuping.ko']
assert hashlib.sha256(module).hexdigest()==prior['touch_module_sha256']
busybox=work/'busybox';busybox.write_bytes(check['bin/busybox']);busybox.chmod(0o755)
for name in ['init','f8-evaluation-report']:
    path=work/(name+'.sh');path.write_bytes(check[name])
    subprocess.run(['qemu-aarch64-static',str(busybox),'sh','-n',str(path)],check=True)
(work/'ramdisk').write_bytes(gzip.compress(helper.cpio_write(new),compresslevel=6,mtime=0))
its=Path('/var/tmp/f8-pro-armbian/official-touch-g3/boot.its').read_text().replace('G3 TOUCH','G4 TOUCH')
(work/'boot.its').write_text(its)
candidate=out/'BOOT_ONLY_ARMBIAN_26.8.1_TOUCH_G4_CANDIDATE.img'
listing=subprocess.check_output(['mkimage','-E','-p','0x800','-f','boot.its',str(candidate)],cwd=work,text=True)
(out/'mkimage.txt').write_text(listing)
data=candidate.read_bytes();tree=fdt(data)
for name in ['kernel','fdt','ramdisk','resource']:
    props=tree['/images/'+name];a=int.from_bytes(props['data-position'],'big');size=int.from_bytes(props['data-size'],'big')
    value=data[a:a+size];assert value==(work/name).read_bytes()
    assert hashlib.sha256(value).digest()==tree['/images/'+name+'/hash']['value']
assert candidate.stat().st_size<64*1024*1024
runtime=struct.unpack_from('<Q',(work/'kernel').read_bytes(),16)[0]
ranges={'kernel':(0x400000,0x400000+runtime),'dtb':(0x8300000,0x8300000+(work/'fdt').stat().st_size+12288),
        'initrd':(0xa200000,0xa200000+(work/'ramdisk').stat().st_size)}
mem=json.loads((P/'analysis/armbian/live-memory-baseline.json').read_text())
banks=[(int(x['base'],16),int(x['base'],16)+int(x['size'],16)) for x in mem['banks']]
for n,(a,b) in ranges.items():assert any(x<=a<b<=y for x,y in banks),n
for n,(a,b) in ranges.items():
    for other,(x,y) in ranges.items():
        if n!=other:assert not(a<y and x<b)
report=copy.deepcopy(prior)
report.update(scope='G3 first-I2C timeout fix: restore factory I2C4 m3 pinmux, hardware retest pending',
              candidate_file=candidate.name,candidate_bytes=candidate.stat().st_size,candidate_sha256=hashlib.sha256(data).hexdigest(),
              log_volume='F8AG4',i2c4_default_mux='m3',i2c4_pins_match_factory=True,
              touch_driver_and_firmware_unchanged=True,touch_dt_only_changes=['I2C4 pinctrl-0','add factory m3 pin group'],
              base_g3_sha256=prior['candidate_sha256'],i2c4_added_group=group,
              diagnostic_improvement='Capture KWin by process and user in addition to parent system unit',
              hardware_test_performed=False,deployment_performed=False,hardware_fix_verified=False)
report['payload_sha256']={name:hashlib.sha256((work/name).read_bytes()).hexdigest()
                          for name in ['kernel','fdt','ramdisk','resource']}
(out/'preflight.json').write_text(json.dumps(report,indent=2)+'\n')
(out/'touch-g4.dtb').write_bytes((work/'fdt').read_bytes())
print(json.dumps({k:report[k] for k in ['candidate_file','candidate_bytes','candidate_sha256','i2c4_default_mux',
      'i2c4_pins_match_factory','touch_driver_and_firmware_unchanged','log_volume','hardware_fix_verified']},indent=2))
