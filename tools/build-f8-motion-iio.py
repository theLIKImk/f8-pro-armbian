"""Build the reference InvenSense IIO drivers and compare import CRCs to official modules."""
import hashlib,json,re,shutil,struct,subprocess
from pathlib import Path
P=Path(__file__).resolve().parents[1]
source=Path('/var/tmp/f8-pro-armbian/linux-rockchip-config/drivers/iio/imu/inv_mpu6050')
headers=Path('/var/tmp/f8-pro-armbian/official-kernel/usr/src/linux-headers-6.1.115-vendor-rk35xx')
root=Path('/var/tmp/f8-pro-armbian/f8-official-armbian-26.8.1/rootfs')
work=Path('/var/tmp/f8-pro-armbian/f8-motion-iio-s1');work.mkdir(exist_ok=True)
out=P/'armbian/motion/official-6.1.115-iio';out.mkdir(exist_ok=True,parents=True)
assert not (out/'module-check.json').exists(),'Preserve completed build'
sources={}
for p in source.iterdir():
    if p.suffix in ['.c','.h']:
        shutil.copyfile(p,work/p.name);sources[p.name]=hashlib.sha256(p.read_bytes()).hexdigest()
(work/'Makefile').write_text('obj-m += inv-mpu6050.o inv-mpu6050-i2c.o\ninv-mpu6050-y := inv_mpu_core.o inv_mpu_ring.o inv_mpu_trigger.o inv_mpu_aux.o inv_mpu_magn.o\ninv-mpu6050-i2c-y := inv_mpu_i2c.o inv_mpu_acpi.o\n')
with (out/'build.log').open('w') as stream:
    r=subprocess.run(['make','-C',str(headers),'M='+str(work),'ARCH=arm64','CROSS_COMPILE=aarch64-linux-gnu-',
        'KERNELRELEASE=6.1.115-vendor-rk35xx','-j2','modules'],stdout=stream,stderr=subprocess.STDOUT)
assert r.returncode==0,(out/'build.log').read_text()[-5000:]
def versions(data):
    assert data[:6]==b'\x7fELF\x02\x01' and struct.unpack_from('<H',data,18)[0]==183
    offset=struct.unpack_from('<Q',data,40)[0];size,count,names=struct.unpack_from('<HHH',data,58)
    sections=[struct.unpack_from('<IIQQQQIIQQ',data,offset+i*size) for i in range(count)]
    ns=sections[names];strings=data[ns[4]:ns[4]+ns[5]]
    section=next((s for s in sections if strings[s[0]:].split(b'\0',1)[0]==b'__versions'),None)
    if section is None:return {}
    body=data[section[4]:section[4]+section[5]];assert len(body)%64==0
    return {body[i+8:i+64].split(b'\0',1)[0].decode():struct.unpack_from('<Q',body,i)[0] for i in range(0,len(body),64)}
known={}
for p in (root/'usr/lib/modules/6.1.115-vendor-rk35xx').rglob('*.ko'):
    for symbol,crc in versions(p.read_bytes()).items():known.setdefault(symbol,set()).add(crc)
mapfile=root/'boot/System.map-6.1.115-vendor-rk35xx'
symbols={f[2]:int(f[0],16) for line in mapfile.read_text().splitlines() if len(f:=line.split())==3}
kernel=(root/'boot/vmlinuz-6.1.115-vendor-rk35xx').read_bytes()
assert hashlib.sha256(kernel).hexdigest()=='a67daf71caefef6b97a22ba708bbb302b239a4a9b4874cadd17a217ebd0c37b7'
base=symbols['_text'];exports={}
for suffix in ['', '_gpl']:
    start=symbols['__start___ksymtab'+suffix];end=symbols['__stop___ksymtab'+suffix]
    crcstart=symbols['__start___kcrctab'+suffix];crcend=symbols['__stop___kcrctab'+suffix]
    assert (end-start)%12==0 and (end-start)//12==(crcend-crcstart)//4
    for symbol,entry in symbols.items():
        if symbol.startswith('__ksymtab_') and start<=entry<end:
            assert (entry-start)%12==0
            exports[symbol[len('__ksymtab_'):]]=struct.unpack_from('<I',kernel,crcstart-base+(entry-start)//12*4)[0]
checked=exports.keys()&known.keys()
assert len(checked)>=10 and all(known[n]=={exports[n]} for n in checked),'Official kernel CRC mapping mismatch'
# Symbols exported by the jointly built core are checked against its modpost output.
local={line.split()[1]:int(line.split()[0],16) for line in (work/'Module.symvers').read_text().splitlines()}
reports=[]
for name in ['inv-mpu6050.ko','inv-mpu6050-i2c.ko']:
    p=work/name;required=versions(p.read_bytes());checks={}
    for symbol,crc in required.items():
        if symbol in local:assert crc==local[symbol];checks[symbol]='jointly-built-core'
        elif symbol in known:assert known[symbol]=={crc},(symbol,crc,known.get(symbol));checks[symbol]='actual-official-module-import'
        else:assert exports.get(symbol)==crc,(symbol,crc,exports.get(symbol));checks[symbol]='actual-official-kernel-export'
    magic=subprocess.check_output(['modinfo','-F','vermagic',str(p)],text=True).strip()
    assert magic.startswith('6.1.115-vendor-rk35xx ') and 'modversions' in magic
    subprocess.run(['aarch64-linux-gnu-strip','--strip-debug',str(p)],check=True);shutil.copyfile(p,out/name)
    reports.append({'file':name,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'vermagic':magic,'imports_verified':checks})
report={'source_directory':str(source),'sources_sha256':sources,'source_modified':False,
 'build_headers_package_version':'26.8.3','headers_not_claimed_exact_image_build':True,
 'all_external_import_crcs_match_actual_26_8_1_kernel':True,'kernel_crc_mapping_cross_checked_symbols':len(checked),'modules':reports,'hardware_loaded':False}
(out/'module-check.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
