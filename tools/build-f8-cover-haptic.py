import ast,hashlib,json,shutil,struct,subprocess
from pathlib import Path
P=Path(__file__).resolve().parents[1]
H=Path('/var/tmp/f8-pro-armbian/official-kernel/usr/src/linux-headers-6.1.115-vendor-rk35xx')
root=Path('/var/tmp/f8-pro-armbian/f8-official-armbian-26.8.1/rootfs')
work=Path('/var/tmp/f8-pro-armbian/f8-cover-haptic-h2');work.mkdir(exist_ok=True)
out=P/'outputs/armbian/f8-cover-haptic-h2';out.mkdir(exist_ok=True);assert not (out/'module-check.json').exists()
source=P/'armbian/input/f8-cover-haptic.c';shutil.copyfile(source,work/source.name)
(work/'Makefile').write_text('obj-m := f8-cover-haptic.o\n')
with (out/'build.log').open('w') as f:r=subprocess.run(['make','-C',str(H),'M='+str(work),'ARCH=arm64','CROSS_COMPILE=aarch64-linux-gnu-','KERNELRELEASE=6.1.115-vendor-rk35xx','-j2','modules'],stdout=f,stderr=subprocess.STDOUT)
assert r.returncode==0,(out/'build.log').read_text()[-5000:]
tree=ast.parse((P/'tools/build-f8-motion-iio.py').read_text());helpers=ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='versions'],type_ignores=[]);exec(compile(helpers,'pure-elf-parser','exec'))
module=work/'f8-cover-haptic.ko';required=versions(module.read_bytes())
symbols={a[2]:int(a[0],16) for line in (root/'boot/System.map-6.1.115-vendor-rk35xx').read_text().splitlines() if len(a:=line.split())==3}
kernel=(root/'boot/vmlinuz-6.1.115-vendor-rk35xx').read_bytes();assert hashlib.sha256(kernel).hexdigest()=='a67daf71caefef6b97a22ba708bbb302b239a4a9b4874cadd17a217ebd0c37b7'
base=symbols['_text'];exports={}
for suffix in ['', '_gpl']:
 start,end=symbols['__start___ksymtab'+suffix],symbols['__stop___ksymtab'+suffix];cs,ce=symbols['__start___kcrctab'+suffix],symbols['__stop___kcrctab'+suffix]
 assert (end-start)//12==(ce-cs)//4
 for name,entry in symbols.items():
  if name.startswith('__ksymtab_') and start<=entry<end:exports[name[10:]]=struct.unpack_from('<I',kernel,cs-base+(entry-start)//12*4)[0]
# ff-memless is a distribution module, not a built-in export in Image.
ff=list((root/'usr/lib/modules/6.1.115-vendor-rk35xx').rglob('ff-memless.ko'));assert len(ff)==1
ffexports={}
for line in (H/'Module.symvers').read_text().splitlines():
 a=line.split()
 if len(a)>=3 and 'ff-memless' in a[2]:ffexports[a[1]]=int(a[0],16)
# Check the module-provided CRC against the shipped provider's __kcrctab.
def export_crc(data,name):
 off=struct.unpack_from('<Q',data,40)[0];size,count,ns=struct.unpack_from('<HHH',data,58);secs=[struct.unpack_from('<IIQQQQIIQQ',data,off+i*size) for i in range(count)];s=secs[ns];names=data[s[4]:s[4]+s[5]]
 for s in secs:
  if names[s[0]:].split(b'\0',1)[0].decode()=='___kcrctab_gpl+'+name:return struct.unpack_from('<I',data,s[4])[0]
 for s in secs:
  if s[1]!=2:continue
  strings=secs[s[6]];table=data[strings[4]:strings[4]+strings[5]]
  for pos in range(s[4],s[4]+s[5],s[9]):
   ni,info,other,section,value,length=struct.unpack_from('<IBBHQQ',data,pos)
   if table[ni:].split(b'\0',1)[0].decode()=='__crc_'+name and section<len(secs):
    target=secs[section];return struct.unpack_from('<I',data,target[4]+value-target[3])[0]
 raise AssertionError('Provider CRC missing: '+name)
checks={}
for name,crc in required.items():
 if name in exports:assert exports[name]==crc,(name,crc,exports[name]);checks[name]='actual Image export'
 elif name in ffexports:assert export_crc(ff[0].read_bytes(),name)==crc;checks[name]='actual shipped ff-memless export'
 else:raise AssertionError('Unverified symbol '+name)
magic=subprocess.check_output(['modinfo','-F','vermagic',str(module)],text=True).strip();assert magic=='6.1.115-vendor-rk35xx SMP mod_unload modversions aarch64'
subprocess.run(['aarch64-linux-gnu-strip','--strip-debug',str(module)],check=True);shutil.copyfile(module,out/module.name)
report={'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'module_sha256':hashlib.sha256(module.read_bytes()).hexdigest(),'vermagic':magic,'all_import_crcs_verified':True,'imports':checks,'loaded':False}
(out/'module-check.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
