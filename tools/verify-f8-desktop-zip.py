"""Verify the Windows-hosted ZIP natively to avoid WSL shared-drive overhead."""
import hashlib
import json
from pathlib import Path
import zipfile
P=Path(__file__).resolve().parents[1]
out=P/'outputs/armbian/official-f8-desktop-t1'
m=json.loads((out/'native-image-manifest.json').read_text())
assert m['root_sha256'] and not m['root_sha256_pending']
target=out/'F8_ARMBIAN_NATIVE_DESKTOP_T1.zip';partial=target.with_suffix('.zip.part')
assert not target.exists() and not (out/'desktop-bundle.json').exists()
rootname='ROOTFS_ARMBIAN_DESKTOP_T1.ext4.img'
names=[rootname,m['boot_file'],'native-image-manifest.json','SHA256SUMS','刷入说明.md','Connect-F8-Desktop.ps1','register-f8-desktop-hostkey.py']
with zipfile.ZipFile(partial) as z:
    assert sorted(z.namelist())==sorted(names) and len(z.namelist())==len(names)
    assert z.getinfo(rootname).file_size==m['root_bytes']
    for name in names:
        with z.open(name) as stream:actual=hashlib.file_digest(stream,'sha256').hexdigest()
        if name==rootname:expected=m['root_sha256']
        elif name==m['boot_file']:expected=m['boot_sha256']
        else:expected=hashlib.sha256((out/name).read_bytes()).hexdigest()
        assert actual==expected,name
        print('Verified '+name,flush=True)
partial.rename(target)
with target.open('rb') as stream:digest=hashlib.file_digest(stream,'sha256').hexdigest()
record={'bundle':target.name,'bytes':target.stat().st_size,'sha256':digest,'all_zip_entries_verified':True,
        'desktop_touch_keyboard_user_confirmed':True,'native_cold_boot_verified':False,'target_partition_written':False,
        'verification_platform':'Windows native Python'}
(out/'desktop-bundle.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps(record,indent=2),flush=True)
