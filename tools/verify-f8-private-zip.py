"""Verify the private rollback ZIP using native Windows reads."""
import hashlib
import json
from pathlib import Path
import zipfile
dest=Path('D:/Netdisk/Other/F8-PRO/private-backups/20261030-original-root')
assert (dest/'PRIVATE-zip-ready.json').exists()
target=dest/'PRIVATE_F8_ORIGINAL_ROLLBACK.zip';partial=target.with_suffix('.zip.part')
assert not target.exists() and not (dest/'PRIVATE-bundle-manifest.json').exists()
m=json.loads((dest/'rollback-manifest.json').read_text())
assert m['fsck_passed'] and m['contains_private_data']
rootname='ROOTFS_ORIGINAL_ROLLBACK.ext4.img';bootname='CURRENT-BOOT-ROLLBACK-64MiB.img'
names=[rootname,bootname,'rollback-manifest.json','SHA256SUMS','PRIVATE-READ-ME.txt']
with zipfile.ZipFile(partial) as z:
    assert sorted(z.namelist())==sorted(names) and len(z.namelist())==len(names)
    assert z.getinfo(rootname).file_size==m['bytes']
    for name in names:
        checksum=hashlib.sha256();count=0;report=1024**3
        with z.open(name) as stream:
            while chunk:=stream.read(4*1024**2):
                checksum.update(chunk);count+=len(chunk)
                if name==rootname and count>=report:
                    print(json.dumps({'private_root_verified_mib':count//1024**2}),flush=True);report+=1024**3
        digest=checksum.hexdigest()
        if name==rootname:assert digest==m['sha256']
        elif name==bootname:assert digest=='7e51e71f7ec7439357e5ea2fbb97118715fe5fcf10401b638609df33567b1dd1'
        elif name=='rollback-manifest.json':assert digest==hashlib.sha256((dest/name).read_bytes()).hexdigest()
        print('Verified private entry: '+name,flush=True)
partial.rename(target)
with target.open('rb') as stream:digest=hashlib.file_digest(stream,'sha256').hexdigest()
result={'bundle':str(target),'bytes':target.stat().st_size,'sha256':digest,'zip_verified':True,'contains_private_data':True,
        'verification_platform':'Windows native Python'}
(dest/'PRIVATE-bundle-manifest.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'private_rollback_exported':True,'bytes':result['bytes'],'sha256':digest}),flush=True)
