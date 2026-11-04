"""Stop the VT2 status service before SDDM takes the screen; BOOT-only patch."""
import gzip,hashlib,importlib.util,json,stat,subprocess,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'tools'))
from inspect_images import fdt
source=P/'outputs/armbian/official-f8-desktop-t1r1/BOOT_ONLY_ARMBIAN_NATIVE_DESKTOP_T1R1.img'
blob=source.read_bytes();assert hashlib.sha256(blob).hexdigest()=='9cc4a4c992130c0e653e10ed22a2c95ba3e9fc7621a2dd8068d7e42ad09d0729'
out=P/'outputs/armbian/official-f8-desktop-t1r2';out.mkdir(exist_ok=True)
assert not (out/'preflight.json').exists()
work=Path('/var/tmp/f8-pro-armbian/desktop-t1r2');work.mkdir(exist_ok=True)
tree=fdt(blob);original={}
for name in ['kernel','fdt','ramdisk','resource']:
    prop=tree['/images/'+name];a=int.from_bytes(prop['data-position'],'big');n=int.from_bytes(prop['data-size'],'big')
    body=blob[a:a+n];assert hashlib.sha256(body).digest()==tree['/images/'+name+'/hash']['value']
    original[name]=body;(work/name).write_bytes(body)
spec=importlib.util.spec_from_file_location('cpio',P/'tools/build-usb-bootlog.py');cpio=importlib.util.module_from_spec(spec);spec.loader.exec_module(cpio)
records=cpio.cpio_read(gzip.decompress(original['ramdisk']))
dropin=b'[Service]\nExecStartPre=/usr/bin/systemctl stop f8-live-status.service\n'
digest=hashlib.sha256(dropin).hexdigest()
patch=f'''# T1r2: the boot VT must relinquish the display before SDDM starts.
handoff=/mnt/root/etc/systemd/system/sddm.service.d/96-f8-status-handoff.conf
mkdir -p /mnt/root/etc/systemd/system/sddm.service.d || fail status-handoff-directory
if [ -e "$handoff" ]; then
    [ ! -L "$handoff" ] || fail status-handoff-symlink
    case "$(sha256sum "$handoff")" in '{digest} '*) ;; *) fail status-handoff-unexpected;; esac
else
    cp /f8-native-status-handoff.conf "$handoff" || fail status-handoff-install
    chmod 0644 "$handoff" || fail status-handoff-mode
fi
echo 'T1r2: stop VT2 status service before SDDM starts; no desktop VT stealing'
'''.encode()
new=[]
for name,values,body in records:
    if name=='init':
        anchor=b'moved=\n';assert body.count(anchor)==1;body=body.replace(anchor,patch+anchor)
    fields=list(values);fields[6]=len(body);new.append((name,fields,body))
new.append(('f8-native-status-handoff.conf',[200001,stat.S_IFREG|0o644,0,0,1,0,len(dropin),0,0,0,0,0,0],dropin))
packed=cpio.cpio_write(new);checked={n:b for n,v,b in cpio.cpio_read(packed)}
assert checked['f8-native-status-handoff.conf']==dropin
busy=work/'busybox';busy.write_bytes(checked['bin/busybox']);busy.chmod(0o755)
init=work/'init.sh';init.write_bytes(checked['init'])
subprocess.run(['qemu-aarch64-static',str(busy),'sh','-n',str(init)],check=True)
assert 'Wants=f8-live-status.service' in Path('/var/tmp/f8-pro-armbian/desktop-t1/rootfs/etc/systemd/system/f8-desktop-hardware.service').read_text()
# Wants permits stopping status without stopping the successful hardware service.
assert 'Requires=f8-live-status.service' not in Path('/var/tmp/f8-pro-armbian/desktop-t1/rootfs/etc/systemd/system/f8-desktop-hardware.service').read_text()
(work/'ramdisk').write_bytes(gzip.compress(packed,compresslevel=6,mtime=0))
(work/'boot.its').write_bytes(Path('/var/tmp/f8-pro-armbian/desktop-t1/native-image/boot.its').read_bytes())
target=out/'BOOT_ONLY_ARMBIAN_NATIVE_DESKTOP_T1R2.img'
subprocess.run(['mkimage','-E','-p','0x800','-f','boot.its',str(target)],cwd=work,check=True,stdout=subprocess.DEVNULL)
data=target.read_bytes();fit=fdt(data)
for name in ['kernel','fdt','ramdisk','resource']:
    prop=fit['/images/'+name];a=int.from_bytes(prop['data-position'],'big');n=int.from_bytes(prop['data-size'],'big');value=data[a:a+n]
    assert value==(work/name).read_bytes() and hashlib.sha256(value).digest()==fit['/images/'+name+'/hash']['value']
    if name!='ramdisk':assert value==original[name]
memory=json.loads((P/'analysis/armbian/live-memory-baseline.json').read_text())
assert any(int(b['base'],16)<=0xa200000 and 0xa200000+len((work/'ramdisk').read_bytes())<=int(b['base'],16)+int(b['size'],16) for b in memory['banks'])
assert len(data)<64*1024**2
record={'file':target.name,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'boot_lba':'0x00008000',
 'rootfs_reflash_required':False,'kernel_dt_resource_unchanged':True,'packed_shell_syntax_verified':True,
 'fit_hashes_and_ramdisk_bank_verified':True,'status_stop_before_sddm':True,'includes_t1r1_offscreen_fix':True,
 'native_t1r1_kwin_gpu_verified':'Mali-G610 MC4 (Panfrost), Mesa26.0.3, Wayland',
 'cold_boot_verified':False,'dropin_sha256':digest}
(out/'preflight.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record,indent=2),flush=True)
