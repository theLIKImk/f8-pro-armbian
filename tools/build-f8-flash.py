"""Build a flash revision and verify import CRCs against the actual kernel Image."""
import argparse,ast,hashlib,json,shutil,struct,subprocess
from pathlib import Path
P=Path(__file__).resolve().parents[1]
H=Path('/var/tmp/f8-pro-armbian/official-kernel/usr/src/linux-headers-6.1.115-vendor-rk35xx')
root=Path('/var/tmp/f8-pro-armbian/f8-official-armbian-26.8.1/rootfs')
parser=argparse.ArgumentParser();parser.add_argument('--revision',choices=['f1','f2'],default='f2');args=parser.parse_args()
work=Path('/var/tmp/f8-pro-armbian/f8-flash-'+args.revision);work.mkdir(exist_ok=True)
out=P/('outputs/armbian/f8-flash-'+args.revision);out.mkdir(parents=True,exist_ok=True)
assert not (out/'module-check.json').exists(),'Preserve completed build'
source=P/('armbian/camera/f8-flash-f2.c' if args.revision=='f2' else 'armbian/camera/f8-flash.c');shutil.copyfile(source,work/'f8-flash.c')
(work/'Makefile').write_text('obj-m := f8-flash.o\n')
with (out/'build.log').open('w') as log:
 r=subprocess.run(['make','-C',str(H),'M='+str(work),'ARCH=arm64','CROSS_COMPILE=aarch64-linux-gnu-','KERNELRELEASE=6.1.115-vendor-rk35xx','-j2','modules'],stdout=log,stderr=subprocess.STDOUT)
assert r.returncode==0,(out/'build.log').read_text()[-6000:]
tree=ast.parse((P/'tools/build-f8-motion-iio.py').read_text())
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='versions'],type_ignores=[]),'elf-parser','exec'))
module=work/'f8-flash.ko';required=versions(module.read_bytes())
symbols={a[2]:int(a[0],16) for line in (root/'boot/System.map-6.1.115-vendor-rk35xx').read_text().splitlines() if len(a:=line.split())==3}
kernel=(root/'boot/vmlinuz-6.1.115-vendor-rk35xx').read_bytes()
assert hashlib.sha256(kernel).hexdigest()=='a67daf71caefef6b97a22ba708bbb302b239a4a9b4874cadd17a217ebd0c37b7'
base=symbols['_text'];exports={}
for suffix in ['', '_gpl']:
 start,end=symbols['__start___ksymtab'+suffix],symbols['__stop___ksymtab'+suffix]
 cs,ce=symbols['__start___kcrctab'+suffix],symbols['__stop___kcrctab'+suffix]
 assert (end-start)//12==(ce-cs)//4
 for name,entry in symbols.items():
  if name.startswith('__ksymtab_') and start<=entry<end:exports[name[10:]]=struct.unpack_from('<I',kernel,cs-base+(entry-start)//12*4)[0]
for name,crc in required.items():assert exports.get(name)==crc,(name,crc,exports.get(name))
magic=subprocess.check_output(['modinfo','-F','vermagic',str(module)],text=True).strip()
assert magic=='6.1.115-vendor-rk35xx SMP mod_unload modversions aarch64'
subprocess.run(['aarch64-linux-gnu-strip','--strip-debug',str(module)],check=True)
shutil.copyfile(module,out/module.name);shutil.copyfile(source,out/source.name)
report={'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'module_sha256':hashlib.sha256(module.read_bytes()).hexdigest(),'vermagic':magic,'all_import_crcs_verified':True,'imports':required,'loaded':False,'gpio':'gpio3 offset17 active-high','pulse_ms':500,'cooldown_ms':500,'variable_brightness':False}
if args.revision=='f2':report.update(revision='f2',cooldown_ms=None,variable_brightness=True,brightness_method='software PWM, nominal 1kHz',max_brightness=100,lease_ms=5000,steady=True,blink=True)
(out/'module-check.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
