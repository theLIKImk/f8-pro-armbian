"""Reconstruct a flashable original filesystem; private files stay in WSL."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tarfile
P = Path(__file__).resolve().parents[1]
work = Path('/var/tmp/f8-pro-armbian/private-backups/20261030-original-root')
os.umask(0o077)
record = json.loads((work/'backup.json').read_text())
archive = Path(record['archive'])
assert record['gzip_crc_verified'] and record['tar_listing_verified']
with archive.open('rb') as stream:
    assert hashlib.file_digest(stream, 'sha256').hexdigest() == record['sha256']
assert not (work/'rollback-manifest.json').exists(), 'Preserve completed rollback'
root = work/'extracted-root'
root.mkdir(exist_ok=False)
# Validate names before privileged extraction; archive was made from our readonly tablet root.
with tarfile.open(archive, 'r:gz') as tf:
    for item in tf:
        assert not item.name.startswith('/') and '..' not in Path(item.name).parts
subprocess.run(['tar','--xattrs','--acls','--numeric-owner','-xzf',str(archive),'-C',str(root)],check=True)
image = work/'ROOTFS_ORIGINAL_ROLLBACK.ext4.img'
with image.open('xb') as stream:
    stream.truncate(16*1024**3)
with (work/'rollback-build.log').open('w') as log:
    subprocess.run(['mkfs.ext4','-F','-L','F8_ARCH_DIAG','-U','e12727f1-9845-42c5-8d74-a2992e855e2a',
        '-O','^orphan_file','-E','lazy_itable_init=0,lazy_journal_init=0','-d',str(root),str(image)],stdout=log,stderr=subprocess.STDOUT,check=True)
    subprocess.run(['e2fsck','-fn',str(image)],stdout=log,stderr=subprocess.STDOUT,check=True)
with image.open('rb') as stream:
    digest = hashlib.file_digest(stream,'sha256').hexdigest()
result = {'image':str(image),'bytes':image.stat().st_size,'sha256':digest,'fsck_passed':True,
    'backup_sha256':record['sha256'],'reconstructed_file_level_not_sector_identical':True,
    'root_lba':'0x00078000','boot_lba':'0x00008000','contains_private_data':True,
    'original_boot':str(P/'outputs/armbian/firstboot-diagnostic/CURRENT-BOOT-ROLLBACK-64MiB.img')}
(work/'rollback-manifest.json').write_text(json.dumps(result,indent=2)+'\n')
(P/'local/hardware/armbian-desktop-t1-live-20261030-01/rollback-manifest.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'rollback_image_verified':True,'bytes':result['bytes'],'sha256':digest}),flush=True)
