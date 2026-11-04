"""Unify FIT/resource DT and defer OTG module until after SSH is available."""
import gzip,hashlib,importlib.util,json,stat,struct,subprocess,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'tools'))
from inspect_images import fdt
base=P/'outputs/armbian/official-f8-native-usb-u1';prior=json.loads((base/'preflight.json').read_text())
assert prior['user_reported_boot_failure']
blob=(base/prior['file']).read_bytes();assert hashlib.sha256(blob).hexdigest()==prior['sha256']
out=P/'outputs/armbian/official-f8-native-usb-u2';out.mkdir(exist_ok=True)
assert not (out/'preflight.json').exists(),'Preserve completed U2'
work=Path('/var/tmp/f8-pro-armbian/native-usb-u2');work.mkdir(exist_ok=True)
tree=fdt(blob);original={}
for name in ['kernel','fdt','ramdisk','resource']:
    v=tree['/images/'+name];a=int.from_bytes(v['data-position'],'big');n=int.from_bytes(v['data-size'],'big')
    original[name]=blob[a:a+n];assert hashlib.sha256(original[name]).digest()==tree['/images/'+name+'/hash']['value']
    (work/name).write_bytes(original[name])
dt=fdt(original['fdt']);assert b'systemd.gpt_auto=0' in dt['/chosen']['bootargs'] and b'f8_usb_u1=1' in dt['/chosen']['bootargs']
# Resource v0: 1-sector header, 1-sector entries, SHA1, then sector-aligned files.
resource=original['resource'];assert resource[:4]==b'RSCE' and resource[4:8]==b'\0'*4 and resource[8:11]==b'\1\1\1'
count=struct.unpack_from('<I',resource,12)[0];assert count==3
entries=[];offset=1+count;result=bytearray(resource[:offset*512]);old_contents={}
for i in range(count):
    entry=bytearray(resource[512+i*512:1024+i*512]);assert entry[:4]==b'ENTR'
    name=entry[4:224].split(b'\0',1)[0].decode();hashlen,pos,size=struct.unpack_from('<3I',entry,256)
    assert hashlen==20 and pos>=count+1 and (pos*512+size)<=len(resource)
    content=resource[pos*512:pos*512+size];assert hashlib.sha1(content).digest()==entry[224:244]
    old_contents[name]=content
    if name=='rk-kernel.dtb':content=original['fdt']
    else:assert name in ['logo.bmp','logo_kernel.bmp']
    entry[224:256]=hashlib.sha1(content).digest()+b'\0'*12
    struct.pack_into('<3I',entry,256,20,offset,len(content))
    result[512+i*512:1024+i*512]=entry
    result.extend(content);result.extend(b'\0'*((-len(result))%512));offset=len(result)//512
assert len(old_contents)==3 and 'rk-kernel.dtb' in old_contents
# Parse the serialized resource again, independent of the entry construction.
for i in range(count):
    entry=result[512+i*512:1024+i*512];name=entry[4:224].split(b'\0',1)[0].decode()
    hashlen,pos,size=struct.unpack_from('<3I',entry,256);value=result[pos*512:pos*512+size]
    assert hashlib.sha1(value).digest()==entry[224:224+hashlen]
    assert value==(original['fdt'] if name=='rk-kernel.dtb' else old_contents[name])
(work/'resource').write_bytes(result)
spec=importlib.util.spec_from_file_location('cpio',P/'tools/build-usb-bootlog.py');cpio=importlib.util.module_from_spec(spec);spec.loader.exec_module(cpio)
records=cpio.cpio_read(gzip.decompress(original['ramdisk']));new=[]
modulemeta=json.loads((P/'outputs/armbian/official-f8-usb-u1-module/module-check.json').read_text())
assert modulemeta['all_import_crcs_match_actual_official_kernel']
digest=modulemeta['sha256']
for name,values,body in records:
    if name=='init':
        old=b'insmod /f8_otg_vbus.ko || fail usb-otg-module\n'
        assert body.count(old)==1
        # No external module load in init, no mandatory USB service dependency.
        patch=f'''# U2: stage only. Load by SSH after a healthy desktop is confirmed.
otg=/mnt/root/usr/libexec/f8-pro/f8_otg_vbus_u2.ko
if [ -e "$otg" ]; then
    [ ! -L "$otg" ] || fail usb-module-symlink
    case "$(sha256sum "$otg")" in '{digest} '*) ;; *) fail usb-module-unexpected;; esac
else
    cp /f8_otg_vbus.ko "$otg" || fail usb-module-stage
    chmod 0644 "$otg" || fail usb-module-mode
fi
'''.encode()
        body=body.replace(old,patch).replace(b'U1 USB2 OTG trial: narrow VBUS driver loaded, power sampler skipped',b'U2 USB2 OTG trial: module staged only, power sampler skipped')
        assert b'\ninsmod ' not in body
    fields=list(values);fields[6]=len(body);new.append((name,fields,body))
packed=cpio.cpio_write(new);check={n:b for n,v,b in cpio.cpio_read(packed)}
assert hashlib.sha256(check['f8_otg_vbus.ko']).hexdigest()==digest
busy=work/'busybox';busy.write_bytes(check['bin/busybox']);busy.chmod(0o755)
(work/'init.sh').write_bytes(check['init']);subprocess.run(['qemu-aarch64-static',str(busy),'sh','-n',str(work/'init.sh')],check=True)
(work/'ramdisk').write_bytes(gzip.compress(packed,compresslevel=6,mtime=0))
(work/'boot.its').write_bytes(Path('/var/tmp/f8-pro-armbian/native-usb-u1/boot.its').read_bytes())
target=out/'BOOT_ONLY_ARMBIAN_NATIVE_USB_U2.img'
subprocess.run(['mkimage','-E','-p','0x800','-f','boot.its',str(target)],cwd=work,check=True,stdout=subprocess.DEVNULL)
data=target.read_bytes();fit=fdt(data)
for name in original:
    v=fit['/images/'+name];a=int.from_bytes(v['data-position'],'big');n=int.from_bytes(v['data-size'],'big');value=data[a:a+n]
    assert value==(work/name).read_bytes() and hashlib.sha256(value).digest()==fit['/images/'+name+'/hash']['value']
    if name in ['kernel','fdt']:assert value==original[name]
memory=json.loads((P/'analysis/armbian/live-memory-baseline.json').read_text())
for name,address,slack in [('fdt',0x8300000,12288),('ramdisk',0xa200000,0)]:
    size=(work/name).stat().st_size+slack
    assert any(int(b['base'],16)<=address and address+size<=int(b['base'],16)+int(b['size'],16) for b in memory['banks'])
assert len(data)<64*1024**2
report={'file':target.name,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'boot_lba':'0x00008000','rootfs_reflash_required':False,'fit_fdt_and_resource_dtb_identical':True,'resource_entry_hashes_verified':True,'logos_unchanged':True,'kernel_and_u1_dt_unchanged':True,'early_insmod_removed':True,'module_staged_only':True,'module_sha256':digest,'power_sampler_skipped_under_u1_marker':True,'usb_module_load_requires_followup_ssh_step':True,'fit_and_memory_verified':True,'cold_boot_verified':False,'usb_flash_enumeration_verified':False,'rollback_file':str(P/'outputs/armbian/official-f8-native-audio-a3/BOOT_ONLY_ARMBIAN_NATIVE_AUDIO_A3.img')}
(out/'preflight.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2),flush=True)
