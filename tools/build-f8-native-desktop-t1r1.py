"""BOOT-only repair: keep the offline EGL diagnostic from gating actual KWin."""
import gzip,hashlib,importlib.util,json,stat,subprocess,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'tools'))
from inspect_images import fdt
source=P/'outputs/armbian/official-f8-desktop-t1/BOOT_NATIVE_ARMBIAN_DESKTOP_T1.img'
blob=source.read_bytes();assert hashlib.sha256(blob).hexdigest()=='3b488ca72b247146d8a8d79fbf1e3481860852fb691707f84fb4abd4606a2c4c'
out=P/'outputs/armbian/official-f8-desktop-t1r1';out.mkdir(exist_ok=True)
assert not (out/'preflight.json').exists()
work=Path('/var/tmp/f8-pro-armbian/desktop-t1r1');work.mkdir(exist_ok=True)
tree=fdt(blob);original={}
for name in ['kernel','fdt','ramdisk','resource']:
    prop=tree['/images/'+name];start=int.from_bytes(prop['data-position'],'big');size=int.from_bytes(prop['data-size'],'big')
    body=blob[start:start+size];assert hashlib.sha256(body).digest()==tree['/images/'+name+'/hash']['value']
    original[name]=body;(work/name).write_bytes(body)
spec=importlib.util.spec_from_file_location('cpio',P/'tools/build-usb-bootlog.py');cpio=importlib.util.module_from_spec(spec);spec.loader.exec_module(cpio)
records=cpio.cpio_read(gzip.decompress(original['ramdisk']));old={n:b for n,v,b in records}
replacement=(P/'armbian/desktop-t1/desktop-hardware.sh').read_bytes()
oldhelper=(P/'armbian/desktop-t1/desktop-hardware.sh').read_bytes().replace(
 b"if ! timeout -k 5 40 python3 -I /usr/libexec/f8-pro/gpu-probe.py --output /run/f8/gpu-result.json; then\n    echo 'Offscreen EGL diagnostic inconclusive; continue to the actual KWin Wayland session'\nfi",
 b'timeout -k 5 40 python3 -I /usr/libexec/f8-pro/gpu-probe.py --output /run/f8/gpu-result.json').replace(
 b'GPU/panel/touch modules loaded; actual rendering must be checked in KWin',b'open GPU pixel acceptance passed')
expected=hashlib.sha256(oldhelper).hexdigest();newhash=hashlib.sha256(replacement).hexdigest()
assert oldhelper==Path('/var/tmp/f8-pro-armbian/desktop-t1/rootfs/usr/libexec/f8-pro/desktop-hardware.sh').read_bytes(), 'Original helper guard must match frozen root'
anchor=b"echo 'Native Armbian root verified; root filesystem writable, partition table unchanged'\n"
assert old['init'].count(anchor)==1
patch=f'''# T1r1: change only the known T1 desktop helper, preserving a rollback copy.
helper=/mnt/root/usr/libexec/f8-pro/desktop-hardware.sh
[ -f "$helper" ] && [ ! -L "$helper" ] || fail desktop-helper-type
current="$(sha256sum "$helper")"
case "$current" in
    '{expected} '*)
        [ -e "$helper.t1-backup" ] || cp -p "$helper" "$helper.t1-backup" || fail helper-backup
        cp /f8-native-desktop-hardware-r1 "$helper" || fail helper-update
        chmod 0755 "$helper" || fail helper-mode
        ;;
    '{newhash} '*) ;;
    *) fail desktop-helper-unexpected-hash ;;
esac
echo 'T1r1 installed: offscreen EGL diagnostic no longer blocks KWin startup'
'''.encode()
new=[]
for name,values,body in records:
    if name=='init':body=body.replace(anchor,anchor+patch)
    fields=list(values);fields[6]=len(body);new.append((name,fields,body))
new.append(('f8-native-desktop-hardware-r1',[200000,stat.S_IFREG|0o755,0,0,1,0,len(replacement),0,0,0,0,0,0],replacement))
packed=cpio.cpio_write(new);checked={n:b for n,v,b in cpio.cpio_read(packed)}
assert checked['f8-native-desktop-hardware-r1']==replacement
busy=work/'busybox';busy.write_bytes(checked['bin/busybox']);busy.chmod(0o755)
for name in ['init','f8-native-desktop-hardware-r1']:
    path=work/(name+'.sh');path.write_bytes(checked[name]);subprocess.run(['qemu-aarch64-static',str(busy),'sh','-n',str(path)],check=True)
(work/'ramdisk').write_bytes(gzip.compress(packed,compresslevel=6,mtime=0))
(work/'boot.its').write_bytes(Path('/var/tmp/f8-pro-armbian/desktop-t1/native-image/boot.its').read_bytes())
target=out/'BOOT_ONLY_ARMBIAN_NATIVE_DESKTOP_T1R1.img'
subprocess.run(['mkimage','-E','-p','0x800','-f','boot.its',str(target)],cwd=work,check=True,stdout=subprocess.DEVNULL)
data=target.read_bytes();fit=fdt(data)
for name in ['kernel','fdt','ramdisk','resource']:
    prop=fit['/images/'+name];a=int.from_bytes(prop['data-position'],'big');n=int.from_bytes(prop['data-size'],'big');value=data[a:a+n]
    assert value==(work/name).read_bytes() and hashlib.sha256(value).digest()==fit['/images/'+name+'/hash']['value']
    if name!='ramdisk':assert value==original[name]
assert len(data)<64*1024**2 and len((work/'ramdisk').read_bytes())<len(original['ramdisk'])+16384
record={'file':target.name,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),
 'boot_lba':'0x00008000','rootfs_reflash_required':False,'kernel_dt_resource_unchanged':True,
 'packed_shell_syntax_verified':True,'fit_hashes_verified':True,'known_original_helper_sha256':expected,
 'replacement_helper_sha256':newhash,'cold_boot_verified':False,'purpose':'Non-gating offscreen EGL diagnostic; actual KWin rendering still requires verification'}
(out/'preflight.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record,indent=2),flush=True)
