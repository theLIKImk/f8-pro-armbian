"""Build narrow OTG regulator and compare every import CRC to actual stock modules."""
import argparse,ast,hashlib,json,re,shutil,struct,subprocess
from pathlib import Path
P=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--diagnostic',action='store_true');parser.add_argument('--passive-addon',action='store_true');args=parser.parse_args()
assert not (args.diagnostic and args.passive_addon)
module_name='f8_otg_status' if args.passive_addon else 'f8_otg_vbus'
H=Path('/var/tmp/f8-pro-armbian/official-kernel/usr/src/linux-headers-6.1.115-vendor-rk35xx')
root=Path('/var/tmp/f8-pro-armbian/f8-official-armbian-26.8.1/rootfs')
suffix='-passive-addon' if args.passive_addon else '-diag' if args.diagnostic else ''
work=Path('/var/tmp/f8-pro-armbian/f8-otg-module-u1'+suffix);work.mkdir(exist_ok=True)
out=P/('outputs/armbian/official-f8-usb-u1-module'+suffix);out.mkdir(exist_ok=True)
assert not (out/'module-check.json').exists(),'Preserve completed module'
source=(P/('armbian/usb/'+module_name+'.c')).read_text()
if args.diagnostic:
    extra='''
/* Passive status only: no ADC start, reset, fault-latch read or policy writes. */
static ssize_t usb_status_show(struct device *dev,
                              struct device_attribute *attr, char *buf)
{
    struct f8_otg *p = dev_get_drvdata(dev);
    static const u8 registers[] = {0x00, 0x02, 0x03, 0x07, 0x0a, 0x0b, 0x11, 0x14};
    int values[ARRAY_SIZE(registers)], i, gpio;
    mutex_lock(&p->lock);
    for (i = 0; i < ARRAY_SIZE(registers); i++) {
        values[i] = i2c_smbus_read_byte_data(p->client, registers[i]);
        if (values[i] < 0) {
            mutex_unlock(&p->lock);
            return values[i];
        }
    }
    gpio = gpiod_get_value_cansleep(p->gate);
    mutex_unlock(&p->lock);
    if (gpio < 0)
        return gpio;
    return sysfs_emit(buf, "reg00=%02x reg02=%02x reg03=%02x reg07=%02x reg0a=%02x reg0b=%02x reg11_cached=%02x reg14=%02x gpio=%d\\n",
                      values[0], values[1], values[2], values[3], values[4], values[5], values[6], values[7], gpio);
}
static DEVICE_ATTR_RO(usb_status);
static struct attribute *f8_usb_status_attrs[] = { &dev_attr_usb_status.attr, NULL };
static const struct attribute_group f8_usb_status_group = { .attrs = f8_usb_status_attrs };
'''
    anchor='static int f8_probe('
    assert source.count(anchor)==1;source=source.replace(anchor,extra+'\n'+anchor)
    anchor='\tdev_info(&client->dev, "OTG-only regulator ready; charger settings preserved\\n");'
    assert source.count(anchor)==1
    source=source.replace(anchor,'\tret = devm_device_add_group(&client->dev, &f8_usb_status_group);\n\tif (ret)\n\t\treturn ret;\n'+anchor)
    (out/'f8_otg_vbus.c').write_text(source)
(work/(module_name+'.c')).write_text(source)
(work/'Makefile').write_text('obj-m := '+module_name+'.o\n')
with (out/'build.log').open('w') as f:
    r=subprocess.run(['make','-C',str(H),'M='+str(work),'ARCH=arm64','CROSS_COMPILE=aarch64-linux-gnu-','KERNELRELEASE=6.1.115-vendor-rk35xx','-j2','modules'],stdout=f,stderr=subprocess.STDOUT)
assert r.returncode==0,(out/'build.log').read_text()[-5000:]
module=work/(module_name+'.ko')
magic=subprocess.check_output(['modinfo','-F','vermagic',str(module)],text=True).strip()
assert magic.startswith('6.1.115-vendor-rk35xx ') and 'modversions' in magic
# Reuse only pure ELF parsing helpers, never the touch builder's top-level code.
syntax=ast.parse((P/'tools/build-f8-official-touch-module.py').read_text())
helpers=ast.Module(body=[n for n in syntax.body if isinstance(n,ast.FunctionDef) and n.name in ['elf_sections','versions']],type_ignores=[])
exec(compile(helpers,'touch-abi-pure-helpers','exec'))
required=versions(module.read_bytes());assert 'module_layout' in required
actual={};provenance={}
for path in sorted((root/'usr/lib/modules/6.1.115-vendor-rk35xx').rglob('*.ko')):
    for name,crc in versions(path.read_bytes()).items():
        if name in required:
            if name in actual:assert actual[name]==crc,name
            actual[name]=crc;provenance[name]=str(path.relative_to(root))
    if required.keys()<=actual.keys():break
# Absolute __crc symbols in the actual image's System.map can cover built-ins
# which no shipped loadable module happens to import. Never use header CRCs.
mapfile=root/'boot/System.map-6.1.115-vendor-rk35xx'
for line in mapfile.read_text().splitlines():
    fields=line.split()
    if len(fields)!=3:continue
    address,kind,name=fields
    if kind.upper()=='A' and name.startswith('__crc_') and name[6:] in required:
        crc=int(address,16)
        assert crc<=0xffffffff
        symbol=name[6:]
        if symbol in actual:assert actual[symbol]==crc
        actual[symbol]=crc;provenance[symbol]=str(mapfile.relative_to(root))
missing=sorted(required.keys()-actual.keys())
if missing:
    symbols={fields[2]:(int(fields[0],16),fields[1]) for line in mapfile.read_text().splitlines() if len(fields:=line.split())==3}
    (out/'kernel-export-layout.json').write_text(json.dumps({n:[hex(v[0]),v[1]] for n,v in symbols.items() if 'kcrctab' in n or 'rdev_get_drvdata' in n or n.startswith('__start___ksymtab') or n.startswith('__stop___ksymtab')},indent=2)+'\n')
    kernel=(root/'boot/vmlinuz-6.1.115-vendor-rk35xx').read_bytes()
    assert hashlib.sha256(kernel).hexdigest()=='a67daf71caefef6b97a22ba708bbb302b239a4a9b4874cadd17a217ebd0c37b7'
    assert kernel[56:60]==b'ARM\x64'
    base=symbols['_text'][0]
    extracted={}
    for name in required:
        symbol=symbols.get('__crc_'+name)
        if symbol is None:continue
        offset=symbol[0]-base
        if 0<=offset<=len(kernel)-4:
            extracted[name]=struct.unpack_from('<I',kernel,offset)[0]
    # Linux 6.1 may omit individual __crc names while retaining parallel
    # sorted __ksymtab (three PREL32 fields) and __kcrctab (u32 CRC) arrays.
    for suffix in ['', '_gpl']:
        start=symbols['__start___ksymtab'+suffix][0]
        end=symbols['__stop___ksymtab'+suffix][0]
        crcstart=symbols['__start___kcrctab'+suffix][0]
        crcend=symbols['__stop___kcrctab'+suffix][0]
        assert (end-start)%12==0 and (end-start)//12==(crcend-crcstart)//4
        for name in required:
            entry=symbols.get('__ksymtab_'+name)
            if entry and start<=entry[0]<end:
                assert (entry[0]-start)%12==0
                index=(entry[0]-start)//12
                offset=crcstart-base+index*4
                extracted[name]=struct.unpack_from('<I',kernel,offset)[0]
    # Validate the virtual-to-file mapping against independent stock module CRCs.
    checked=extracted.keys()&actual.keys()
    (out/'kernel-crc-mapping.json').write_text(json.dumps({'base':hex(base),'checked_count':len(checked),'symbols':{n:{'symbol':symbols.get('__crc_'+n),'raw':hex(extracted[n]) if n in extracted else None,'stock':hex(actual[n]) if n in actual else None} for n in required},'text_symbols':{n:symbols.get(n) for n in ['_text','_stext','_head','__start___kcrctab','__stop___kcrctab']}},indent=2)+'\n')
    assert len(checked)>=10 and all(extracted[n]==actual[n] for n in checked), 'Kernel CRC mapping not independently verified'
    for name in missing:
        if name in extracted:
            actual[name]=extracted[name];provenance[name]='actual official vmlinuz __crc address from System.map; mapping cross-checked against '+str(len(checked))+' stock module CRCs'
    missing=sorted(required.keys()-actual.keys())
mismatch=[n for n in required.keys()&actual.keys() if required[n]!=actual[n]]
(out/'actual-official-abi.json').write_text(json.dumps({'required':{n:hex(c) for n,c in required.items()},'provenance':provenance,'missing':missing,'mismatches':mismatch},indent=2)+'\n')
assert not missing and not mismatch,(missing,mismatch)
subprocess.run(['aarch64-linux-gnu-strip','--strip-debug',str(module)],check=True)
shutil.copyfile(module,out/module.name)
report={'module':module.name,'bytes':module.stat().st_size,'sha256':hashlib.sha256(module.read_bytes()).hexdigest(),'vermagic':magic,'all_import_crcs_match_actual_official_kernel':True,'import_count':len(required),'loaded':False,'hardware_tested':False,'source_sha256':hashlib.sha256((work/(module_name+'.c')).read_bytes()).hexdigest(),'scope':'Passive fixed-client USB status addon; no writes' if args.passive_addon else 'Custom OTG-only regulator; no charger initialization, not deployed'}
(out/'module-check.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
