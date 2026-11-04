import ast,hashlib,json,shutil,struct,subprocess
from pathlib import Path
P=Path(__file__).resolve().parents[1]
H=Path('/var/tmp/f8-pro-armbian/official-kernel/usr/src/linux-headers-6.1.115-vendor-rk35xx')
root=Path('/var/tmp/f8-pro-armbian/f8-official-armbian-26.8.1/rootfs')
W=Path('/var/tmp/f8-pro-armbian/f8-sensor-relay-r1');W.mkdir(exist_ok=True)
O=P/'outputs/armbian/f8-sensor-relay-r1';O.mkdir(parents=True,exist_ok=True)
shutil.copyfile(P/'armbian/sensor-relay/f8_sensor_relay.c',W/'f8_sensor_relay.c')
(W/'Makefile').write_text('obj-m := f8_sensor_relay.o\n')
with (O/'build.log').open('w') as log:r=subprocess.run(['make','-C',str(H),'M='+str(W),'ARCH=arm64','CROSS_COMPILE=aarch64-linux-gnu-','KERNELRELEASE=6.1.115-vendor-rk35xx','-j2','modules'],stdout=log,stderr=subprocess.STDOUT)
assert r.returncode==0,(O/'build.log').read_text()[-3500:]
tree=ast.parse((P/'tools/build-f8-motion-iio.py').read_text())
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='versions'],type_ignores=[]),'elf-parser','exec'))
module=W/'f8_sensor_relay.ko';required=versions(module.read_bytes())
symbols={a[2]:int(a[0],16) for line in (root/'boot/System.map-6.1.115-vendor-rk35xx').read_text().splitlines() if len(a:=line.split())==3}
kernel=(root/'boot/vmlinuz-6.1.115-vendor-rk35xx').read_bytes();assert hashlib.sha256(kernel).hexdigest()=='a67daf71caefef6b97a22ba708bbb302b239a4a9b4874cadd17a217ebd0c37b7'
exports={};base=symbols['_text']
for suffix in ['', '_gpl']:
 start,end=symbols['__start___ksymtab'+suffix],symbols['__stop___ksymtab'+suffix];cs,ce=symbols['__start___kcrctab'+suffix],symbols['__stop___kcrctab'+suffix]
 assert (end-start)//12==(ce-cs)//4
 for name,entry in symbols.items():
  if name.startswith('__ksymtab_') and start<=entry<end:exports[name[10:]]=struct.unpack_from('<I',kernel,cs-base+(entry-start)//12*4)[0]
for name,crc in required.items():assert exports.get(name)==crc,(name,crc,exports.get(name))
magic=subprocess.check_output(['modinfo','-F','vermagic',str(module)],text=True).strip();assert magic=='6.1.115-vendor-rk35xx SMP mod_unload modversions aarch64'
subprocess.run(['aarch64-linux-gnu-strip','--strip-debug',str(module)],check=True)
shutil.copyfile(module,O/'f8_sensor_relay.ko')
report={'sha256':hashlib.sha256(module.read_bytes()).hexdigest(),'srcversion':subprocess.check_output(['modinfo','-F','srcversion',str(module)],text=True).strip(),'vermagic':magic,'all_import_crcs_verified_against_actual_image':True,'imports':required}
(O/'module-check.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
