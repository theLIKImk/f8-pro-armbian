"""C4 BOOT-only, hash-gated R1 account repair and deferred guarded p6 resize."""
from pathlib import Path
import gzip,hashlib,importlib.util,json,os,stat,subprocess,sys
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'tools'))
from inspect_images import fdt
def sha(b):return hashlib.sha256(b).hexdigest()
source=P/'outputs/armbian/official-f8-camera-c4/BOOT_ONLY_ARMBIAN_CAMERA_C4.img';blob=source.read_bytes()
assert sha(blob)=='fbbfa1ece55b3c62decbd10ae9c2ac98ed5d717dd5f8b941c49004deb6c0903a'
O=P/'outputs/armbian/f8-first-run-r1a';O.mkdir(exist_ok=True)
assert not (O/'preflight.json').exists()
B=Path('/var/tmp/f8-pro-armbian/first-run-r1a');B.mkdir(exist_ok=True)
oldtree=fdt(blob);original={}
for name in ['kernel','fdt','resource','ramdisk']:
 q=oldtree['/images/'+name];a=int.from_bytes(q['data-position'],'big');n=int.from_bytes(q['data-size'],'big');body=blob[a:a+n]
 assert hashlib.sha256(body).digest()==oldtree['/images/'+name+'/hash']['value']
 original[name]=body;(B/name).write_bytes(body)
s=importlib.util.spec_from_file_location('cpio',P/'tools/build-usb-bootlog.py');c=importlib.util.module_from_spec(s);s.loader.exec_module(c)
records=c.cpio_read(gzip.decompress(original['ramdisk']));assets={
 'f8-r1a-apply.py':(P/'armbian/first-run/first-run-apply.py').read_bytes(),
 'f8-r1a-grow.py':(P/'armbian/first-run/root-grow-r1a.py').read_bytes(),
 'f8-root-grow-r1a.service':(P/'armbian/first-run/f8-root-grow-r1a.service').read_bytes()}
oldhelper='4e6b521190ebbc65e7077eb622f02e807f61a68561f11acade8142e2244e5108';newhelper=sha(assets['f8-r1a-apply.py'])
patch=f'''# R1a: repair the first-run helper only on the new R1 root.
if [ -f /mnt/root/etc/f8-pro-release-r1 ]; then
    helper=/mnt/root/usr/local/lib/f8-pro/first-run-apply.py
    [ -f "$helper" ] && [ ! -L "$helper" ] || fail r1a-helper-type
    case "$(sha256sum "$helper")" in
        '{oldhelper} '*)
            mkdir -p /mnt/root/var/lib/f8-pro/first-run || fail r1a-backup-dir
            backup=/mnt/root/var/lib/f8-pro/first-run/helper-before-r1a.py
            [ -e "$backup" ] || cp -p "$helper" "$backup" || fail r1a-backup
            cp /f8-r1a-apply.py "$helper.r1a-new" || fail r1a-helper-copy
            chmod 0755 "$helper.r1a-new" || fail r1a-helper-mode
            chown 0:0 "$helper.r1a-new" || fail r1a-helper-owner
            mv "$helper.r1a-new" "$helper" || fail r1a-helper-rename
            ;;
        '{newhelper} '*) ;;
        *) fail r1a-helper-unexpected-hash ;;
    esac
'''
for asset,target,mode in [('f8-r1a-grow.py','/usr/local/lib/f8-pro/root-grow-r1a.py','0755'),('f8-root-grow-r1a.service','/etc/systemd/system/f8-root-grow-r1a.service','0644')]:
 digest=sha(assets[asset]);dest='/mnt/root'+target
 patch+=f'''    destination={dest}
    if [ -e "$destination" ]; then
        [ -f "$destination" ] && [ ! -L "$destination" ] || fail r1a-asset-type
        case "$(sha256sum "$destination")" in '{digest} '*) ;; *) fail r1a-asset-unexpected;; esac
    else
        cp /{asset} "$destination" || fail r1a-asset-copy
        chmod {mode} "$destination" || fail r1a-asset-mode
        chown 0:0 "$destination" || fail r1a-asset-owner
    fi
'''
patch+='''    wanted=/mnt/root/etc/systemd/system/f8-desktop.target.wants
    mkdir -p "$wanted" || fail r1a-wants-dir
    if [ -e "$wanted/f8-root-grow-r1a.service" ] || [ -L "$wanted/f8-root-grow-r1a.service" ]; then
        [ "$(readlink "$wanted/f8-root-grow-r1a.service")" = '../f8-root-grow-r1a.service' ] || fail r1a-wants-unexpected
    else
        ln -s ../f8-root-grow-r1a.service "$wanted/f8-root-grow-r1a.service" || fail r1a-enable-grow
    fi
    echo 'R1a: helper repaired; verified ext4 expansion deferred until after SDDM'
fi
'''
patch=patch.encode();new=[]
for name,v,body in records:
 if name=='init':
  anchor=b'moved=\n';assert body.count(anchor)==1;body=body.replace(anchor,patch+anchor)
 fields=list(v);fields[6]=len(body);new.append((name,fields,body))
for i,(name,body) in enumerate(assets.items()):new.append((name,[300001+i,stat.S_IFREG|0o644,0,0,1,0,len(body),0,0,0,0,0,0],body))
packed=c.cpio_write(new);checked={n:b for n,v,b in c.cpio_read(packed)}
assert len(checked)==len(records)+len(assets)
for name,v,body in records:
 if name=='init':assert checked[name].replace(patch,b'',1)==body
 else:assert checked[name]==body,name
busy=B/'busybox';busy.write_bytes(checked['bin/busybox']);busy.chmod(0o755)
(B/'init.sh').write_bytes(checked['init']);(O/'patch-init.sh').write_bytes(patch)
subprocess.run(['qemu-aarch64-static',str(busy),'sh','-n',str(B/'init.sh')],check=True)
applets=subprocess.check_output(['qemu-aarch64-static',str(busy),'--list'],text=True).split()
assert all(x in applets for x in ['cp','chmod','chown','mv','ln','sha256sum','readlink'])
(B/'ramdisk').write_bytes(gzip.compress(packed,compresslevel=6,mtime=0));(B/'boot.its').write_bytes((P/'armbian/camera/boot-c4.its').read_bytes())
target=O/'BOOT_ONLY_F8_ARMBIAN_R1A_SETUP_GROW.img'
subprocess.run(['mkimage','-E','-p','0x800','-f','boot.its',str(target)],cwd=B,check=True,stdout=subprocess.DEVNULL,env=dict(os.environ,SOURCE_DATE_EPOCH=str(int.from_bytes(oldtree['/']['timestamp'],'big'))))
final=target.read_bytes();tree=fdt(final)
for name in original:
 q=tree['/images/'+name];a=int.from_bytes(q['data-position'],'big');n=int.from_bytes(q['data-size'],'big');body=final[a:a+n]
 assert body==(B/name).read_bytes() and hashlib.sha256(body).digest()==tree['/images/'+name+'/hash']['value']
 if name!='ramdisk':assert body==original[name]
memory=json.loads((P/'analysis/armbian/live-memory-baseline.json').read_text());a=0xa200000;n=(B/'ramdisk').stat().st_size
assert any(int(b['base'],16)<=a and a+n<=int(b['base'],16)+int(b['size'],16) for b in memory['banks'])
assert len(final)<64*1024**2
record={'file':target.name,'bytes':len(final),'sha256':sha(final),'boot_lba':'0x00008000','kernel_dt_resource_identical_to_C4':True,'rootfs_reflash_required':False,'helper_before_sha256':oldhelper,'helper_after_sha256':newhelper,'assets':{n:sha(b) for n,b in assets.items()},'fit_hashes_shell_memory_verified':True,'deferred_root_expansion':True,'partition_table_changes':False,'cold_boot_verified':False,'device_written':False}
(O/'preflight.json').write_text(json.dumps(record,indent=2)+'\n');(O/'SHA256SUMS').write_text(sha(final)+'  '+target.name+'\n');print(json.dumps(record,indent=2))
