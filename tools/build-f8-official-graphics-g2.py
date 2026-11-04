"""Targeted G1 GPU-domain regulator fix; keep official kernel and root unchanged."""
import copy
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import struct
import subprocess
import sys
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'tools'))
from inspect_images import fdt
base=P/'outputs/armbian/official-f8-graphics-r1b/boot-g1b'
out=P/'outputs/armbian/official-f8-graphics-g2';out.mkdir(exist_ok=True)
assert not (out/'preflight.json').exists(),'Preserve completed G2'
previous=json.loads((base/'preflight.json').read_text())
image=base/previous['candidate_file'];blob=image.read_bytes()
assert hashlib.sha256(blob).hexdigest()==previous['candidate_sha256']=='0eddfc105ff790687bc96a84cb580ffb1ca2ba6ee7823fa121beec2510943926'
fit=fdt(blob)
work=Path('/var/tmp/f8-pro-armbian/official-graphics-g2');work.mkdir(exist_ok=True)
for name in ['kernel','fdt','ramdisk','resource']:
    props=fit['/images/'+name];start=int.from_bytes(props['data-position'],'big');size=int.from_bytes(props['data-size'],'big')
    data=blob[start:start+size];assert hashlib.sha256(data).digest()==fit['/images/'+name+'/hash']['value']
    (work/name).write_bytes(data)
before=fdt((work/'fdt').read_bytes())
controller='/power-management@fd8d8000/power-controller'
rail='/spi@feb20000/rk806single@0/regulators/DCDC_REG1'
assert 'gpu-supply' not in before[controller]
handle=int.from_bytes(before[rail]['phandle'],'big')
subprocess.run(['fdtput','-t','x',str(work/'fdt'),controller,'gpu-supply',format(handle,'x')],check=True)
subprocess.run(['fdtput','-t','s',str(work/'fdt'),'/','model','F8-PRO official Armbian GPU/display G2 domain supply fix'],check=True)
after=fdt((work/'fdt').read_bytes())
expected=copy.deepcopy(before)
expected[controller]['gpu-supply']=before[rail]['phandle']
expected['/']['model']=b'F8-PRO official Armbian GPU/display G2 domain supply fix\0'
assert after==expected,'Only GPU-domain supply and model may change'
assert after['/gpu-panthor@fb000000']['mali-supply']==after[controller]['gpu-supply']
assert after[rail]==before[rail],'Voltage constraints/always-on policy must stay unchanged'
spec=importlib.util.spec_from_file_location('cpio_helper',P/'tools/build-usb-bootlog.py')
helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
records=helper.cpio_read(gzip.decompress((work/'ramdisk').read_bytes()))
fat=work/'logs.img'
with fat.open('wb') as stream:stream.truncate(16*1024*1024)
subprocess.run(['mkfs.vfat','-n','F8AG2',str(fat)],check=True,stdout=subprocess.DEVNULL)
subprocess.run(['fsck.vfat','-n',str(fat)],check=True,stdout=subprocess.DEVNULL)
new=[];changed=[]
for name,values,body in records:
    data=body
    if name in ['init','f8-evaluation-report']:
        data=body.replace(b'ARMBIAN-G1',b'ARMBIAN-G2').replace(b'F8PROAG1',b'F8PROAG2').replace(b'f8_official_armbian_g1',b'f8_official_armbian_g2')
    elif name=='f8-firstboot-logs.img':data=fat.read_bytes()
    if data!=body:changed.append(name)
    fields=list(values);fields[6]=len(data);new.append((name,fields,data))
assert sorted(changed)==['f8-evaluation-report','f8-firstboot-logs.img','init']
cpio=helper.cpio_write(new)
check={n:b for n,_,b in helper.cpio_read(cpio)}
for name,_,body in records:
    if name not in changed:assert check[name]==body,name
(work/'ramdisk').write_bytes(gzip.compress(cpio,compresslevel=6,mtime=0))
busybox=work/'busybox';busybox.write_bytes(check['bin/busybox']);busybox.chmod(0o755)
for name in ['init','f8-evaluation-report']:
    source=work/(name+'.sh');source.write_bytes(check[name])
    subprocess.run(['qemu-aarch64-static',str(busybox),'sh','-n',str(source)],check=True)
subprocess.run(['dtc','-I','dtb','-O','dtb','-o',str(work/'checked.dtb'),str(work/'fdt')],check=True,capture_output=True)
assert fdt((work/'checked.dtb').read_bytes())==after
its=Path('/var/tmp/f8-pro-armbian/official-graphics-boot-r1/boot.its').read_text()
(work/'boot.its').write_text(its.replace('GPU/display NOT APPROVED','GPU/display G2 NOT APPROVED'))
candidate=out/'BOOT_ONLY_ARMBIAN_26.8.1_GPU_G2_CANDIDATE.img'
listing=subprocess.check_output(['mkimage','-E','-p','0x800','-f','boot.its',str(candidate)],cwd=work,text=True)
(out/'mkimage.txt').write_text(listing)
final=candidate.read_bytes();tree=fdt(final)
for name in ['kernel','fdt','ramdisk','resource']:
    props=tree['/images/'+name];a=int.from_bytes(props['data-position'],'big');size=int.from_bytes(props['data-size'],'big')
    data=final[a:a+size]
    assert data==(work/name).read_bytes() and hashlib.sha256(data).digest()==tree['/images/'+name+'/hash']['value']
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
report=copy.deepcopy(previous)
report.update(scope='Targeted GPU domain-supply fix based on G1 pstore panic; hardware retest pending',
              candidate_file=candidate.name,candidate_bytes=candidate.stat().st_size,
              candidate_sha256=hashlib.sha256(final).hexdigest(),log_volume='F8AG2',
              gpu_domain_supply_path=rail,gpu_domain_supply_verified=True,
              voltage_constraints_unchanged=True,panic_guard_unchanged=True,
              other_dt_properties_unchanged=True,official_kernel_unchanged=True,rootfs_unchanged=True,
              initramfs_only_changed_files=changed,g1_hardware_failed=True,
              hardware_fix_verified=False,hardware_test_performed=False,deployment_performed=False,
              fit_payload_hashes_verified=True,layout_with_12k_pad_verified=True)
(out/'preflight.json').write_text(json.dumps(report,indent=2)+'\n')
(out/'graphics-g2.dtb').write_bytes((work/'fdt').read_bytes())
print(json.dumps({k:report[k] for k in ['candidate_file','candidate_bytes','candidate_sha256','gpu_domain_supply_path',
      'voltage_constraints_unchanged','rootfs_unchanged','log_volume','hardware_fix_verified']},indent=2))
