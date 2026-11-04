"""Export a verified private rollback ZIP into a pre-protected Windows folder."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import zipfile
work=Path('/var/tmp/f8-pro-armbian/private-backups/20261030-original-root')
m=json.loads((work/'rollback-manifest.json').read_text())
image=Path(m['image']);boot=Path(m['original_boot'])
assert m['fsck_passed']
assert subprocess.check_output(['blkid','-s','UUID','-o','value',str(image)],text=True).strip()=='e12727f1-9845-42c5-8d74-a2992e855e2a'
for required in ['/etc/arch-release','/etc/fstab','/etc/ssh/ssh_host_ed25519_key',
                 '/var/lib/f8-pro/armbian-official-26.8.1/rootfs.squashfs']:
    check=subprocess.run(['debugfs','-R','stat '+required,str(image)],capture_output=True,text=True,check=True)
    assert 'Inode:' in check.stdout,required
    if required.endswith('rootfs.squashfs'):
        assert int(re.search(r'Size:\s+(\d+)',check.stdout).group(1))==2148360192
m['root_uuid_and_critical_paths_verified']=True
(work/'rollback-manifest.json').write_text(json.dumps(m,indent=2)+'\n')
assert hashlib.sha256(boot.read_bytes()).hexdigest()=='7e51e71f7ec7439357e5ea2fbb97118715fe5fcf10401b638609df33567b1dd1'
dest=Path('/mnt/d/Netdisk/Other/F8-PRO/private-backups/20261030-original-root')
assert (dest/'OWNER_ONLY_DIRECTORY.txt').is_file(), 'Create owner-only Windows ACL before exporting'
target=dest/'PRIVATE_F8_ORIGINAL_ROLLBACK.zip';partial=target.with_suffix('.zip.part')
assert not target.exists() and not partial.exists()
print('Exporting private rollback ZIP64',flush=True)
with zipfile.ZipFile(partial,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=1,allowZip64=True) as z:
    z.write(image,image.name);z.write(boot,boot.name)
    z.write(work/'rollback-manifest.json','rollback-manifest.json')
    z.writestr('SHA256SUMS',m['sha256']+'  '+image.name+'\n7e51e71f7ec7439357e5ea2fbb97118715fe5fcf10401b638609df33567b1dd1  '+boot.name+'\n')
    z.writestr('PRIVATE-READ-ME.txt','PRIVATE BACKUP: includes original Wi-Fi, SSH and user data.\nRestore in Loader only: ROOTFS at sector 0x00078000, BOOT at sector 0x00008000.\nFilesystem reconstructed from verified file-level archive, not a sector clone.\n')
(dest/'rollback-manifest.json').write_text(json.dumps(m,indent=2)+'\n')
(dest/'PRIVATE-zip-ready.json').write_text(json.dumps({'partial':partial.name,'verification_pending':True})+'\n')
print('Private ZIP written; run native Windows verifier before use',flush=True)
