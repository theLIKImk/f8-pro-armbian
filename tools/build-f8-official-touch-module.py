"""Build a uniquely named F8 module; verify imports against official 26.8.1 modules."""
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import struct
import subprocess

P=Path('/mnt/d/Netdisk/Other/F8-PRO/archlinux')
E=P/'analysis/armbian/official-gpu-baseline-20261029/touch-abi'
root=Path('/var/tmp/f8-pro-armbian/f8-official-armbian-26.8.1/rootfs')
headers=Path('/var/tmp/f8-pro-armbian/official-kernel/usr/src/linux-headers-6.1.115-vendor-rk35xx')
source=Path('/var/tmp/f8-pro-armbian/linux-rockchip-config/drivers/input/touchscreen')
work=Path('/var/tmp/f8-pro-armbian/f8-official-touch-module-v1');work.mkdir(exist_ok=True)
out=P/'armbian/touch/official-6.1.115-f8';out.mkdir(exist_ok=True)
assert not (out/'module-check.json').exists(),'Preserve completed module build'
candidate=P/'armbian/touch/candidate-r8-shuping/gsl3673.c'
assert hashlib.sha256(candidate.read_bytes()).hexdigest()=='d7822db00ca3703a0ae439940b8eff1951dc87253db1476fc82e08f941220661'
driver=candidate.read_text()
driver=driver.replace('#define GSL3673_I2C_NAME\t"gsl3673"','#define GSL3673_I2C_NAME\t"f8-gsl-shuping"')
assert '"f8-gsl-shuping"' in driver
old='\t{.compatible = "GSL,GSL3673", .data = &gsl_generic_profile},\n'
assert old in driver;driver=driver.replace(old,'')
old='\tif (!ts->profile)\n\t\tts->profile = &gsl_generic_profile;'
assert old in driver;driver=driver.replace(old,'\tif (!ts->profile || !ts->profile->evaluation)\n\t\treturn -ENODEV;')
driver=driver.replace('MODULE_DEVICE_TABLE(i2c, gsl_ts_id);','MODULE_DEVICE_TABLE(i2c, gsl_ts_id);\nMODULE_DEVICE_TABLE(of, gsl_ts_ids);')
driver=driver.replace('MODULE_ALIAS("platform:gsl_ts");','')
for filename,data in [('f8_gsl_driver.c',driver.encode()),
                      ('gsl_point_id.c',(source/'gsl_point_id.c').read_bytes()),
                      ('gsl_point_id.h',(source/'gsl_point_id.h').read_bytes()),
                      ('f8-pro-r8-shuping-reference.h',(P/'armbian/touch/reference-r8-shuping/f8-pro-r8-shuping-reference.h').read_bytes())]:
    (work/filename).write_bytes(data);(out/filename).write_bytes(data)
(work/'Makefile').write_text('obj-m := f8_gsl_shuping.o\nf8_gsl_shuping-y := f8_gsl_driver.o gsl_point_id.o\nccflags-y += -I'+str(source)+'\n')
command=['make','-C',str(headers),'M='+str(work),'ARCH=arm64','CROSS_COMPILE=aarch64-linux-gnu-',
         'KERNELRELEASE=6.1.115-vendor-rk35xx','-j2','modules']
with (out/'build.log').open('w') as stream:
    result=subprocess.run(command,stdout=stream,stderr=subprocess.STDOUT)
assert result.returncode==0,(out/'build.log').read_text()[-5000:]
module=work/'f8_gsl_shuping.ko'
info=subprocess.check_output(['modinfo',str(module)],text=True)
(out/'modinfo.txt').write_text(info)
magic=subprocess.check_output(['modinfo','-F','vermagic',str(module)],text=True).strip()
assert magic.startswith('6.1.115-vendor-rk35xx ') and 'modversions' in magic
assert 'f8-pro,gslx680-shuping-eval' in info
assert 'GSL,GSL3673' not in info
def elf_sections(data):
    assert data[:6]==b'\x7fELF\x02\x01' and struct.unpack_from('<H',data,18)[0]==183
    offset=struct.unpack_from('<Q',data,40)[0]
    size,count,names=struct.unpack_from('<HHH',data,58)
    sections=[struct.unpack_from('<IIQQQQIIQQ',data,offset+i*size) for i in range(count)]
    ns=sections[names];strings=data[ns[4]:ns[4]+ns[5]]
    return {strings[s[0]:].split(b'\0',1)[0].decode():s for s in sections}
def versions(data):
    section=elf_sections(data).get('__versions')
    if not section:return {}
    body=data[section[4]:section[4]+section[5]];assert len(body)%64==0
    result={}
    for pos in range(0,len(body),64):
        crc=struct.unpack_from('<Q',body,pos)[0];assert crc<=0xffffffff
        name=body[pos+8:pos+64].split(b'\0',1)[0].decode()
        assert re.fullmatch('[A-Za-z0-9_]+',name)
        result[name]=crc
    return result
required=versions(module.read_bytes());assert 'module_layout' in required
stock=list((root/'usr/lib/modules/6.1.115-vendor-rk35xx').rglob('*gsl*.ko'))
allmods=sorted((root/'usr/lib/modules/6.1.115-vendor-rk35xx').rglob('*.ko'))
seen=set();actual={};provenance={}
for path in [*stock,*allmods]:
    if path in seen:continue
    seen.add(path)
    for name,crc in versions(path.read_bytes()).items():
        if name not in required:continue
        if name in actual:assert actual[name]==crc,name
        else:actual[name]=crc;provenance[name]=str(path.relative_to(root))
    if required.keys()<=actual.keys():break
missing=sorted(required.keys()-actual.keys())
mismatched=[name for name in required.keys()&actual.keys() if required[name]!=actual[name]]
abi={'required_symbols':{n:hex(c) for n,c in required.items()},
     'actual_official_reference_modules':provenance,'missing':missing,'mismatches':mismatched}
(out/'actual-official-abi.json').write_text(json.dumps(abi,indent=2)+'\n')
assert not missing and not mismatched,abi
# Verify serialized board data after full module linking (not only a driver .o).
data=module.read_bytes();sections=elf_sections(data)
symbols=subprocess.check_output(['aarch64-linux-gnu-nm','-S','--defined-only',str(module)],text=True)
arrays=[]
for symbol,section,reference in [('f8_pro_r8_shuping_fw','.rodata','firmware-reference.bin'),
                                ('f8_pro_r8_shuping_algorithm','.data','algorithm-reference.bin')]:
    line=next(s for s in symbols.splitlines() if s.endswith(' '+symbol))
    fields=line.split();offset=int(fields[0],16);size=int(fields[1],16);entry=sections[section]
    compiled=data[entry[4]+offset:entry[4]+offset+size]
    expected=(P/'armbian/touch/reference-r8-shuping'/reference).read_bytes()
    assert compiled==expected,symbol
    arrays.append({'name':symbol,'bytes':size,'sha256':hashlib.sha256(compiled).hexdigest()})
assert all(s.endswith(' gsl_DataInit') or 'gsl_DataInit' not in s for s in symbols.splitlines())
subprocess.run(['aarch64-linux-gnu-strip','--strip-debug',str(module)],check=True)
shutil.copyfile(module,out/module.name)
report={'scope':'Full F8 driver+algorithm module link and actual official import CRC checks; not loaded',
        'module':module.name,'bytes':module.stat().st_size,'sha256':hashlib.sha256(module.read_bytes()).hexdigest(),
        'target_official_image_version':'26.8.1','build_headers_package_version':'26.8.3',
        'headers_not_claimed_exact_image_build':True,'vermagic':magic,
        'imported_symbol_count':len(required),'all_import_crcs_match_actual_official_modules':True,
        'kernel_module_layout_crc_matches':True,'linked_board_arrays':arrays,
        'unique_i2c_driver_name':'f8-gsl-shuping','of_match':'f8-pro,gslx680-shuping-eval',
        'algorithm_linked_privately':True,'algorithm_source_sha256':hashlib.sha256((source/'gsl_point_id.c').read_bytes()).hexdigest(),
        'hardware_loaded':False,'controller_written':False,'remaining':['Algorithm identity/version review','IRQ/reset/coordinate hardware trial']}
(out/'module-check.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
