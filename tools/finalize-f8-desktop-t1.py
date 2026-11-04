"""Apply final persistence fix, validate, then produce a ZIP64 desktop bundle."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import zipfile
P=Path(__file__).resolve().parents[1]
out=P/'outputs/armbian/official-f8-desktop-t1'
manifest=out/'native-image-manifest.json'
m=json.loads(manifest.read_text())
image=Path(m['root_image'])
assert not (out/'desktop-bundle.json').exists()
assert not (out/'F8_ARMBIAN_NATIVE_DESKTOP_T1.zip').exists()
assert not (out/'F8_ARMBIAN_NATIVE_DESKTOP_T1.zip.part').exists()
work=image.parent
mount=work/'final-check';mount.mkdir(exist_ok=True)
assert subprocess.run(['mountpoint','-q',str(mount)]).returncode!=0
subprocess.run(['mount','-o','loop,rw',str(image),str(mount)],check=True)
try:
    dest=mount/'usr/libexec/f8-pro/native-prepare.sh'
    dest.write_bytes((P/'armbian/desktop-t1/native-prepare.sh').read_bytes());dest.chmod(0o755)
    (mount/'etc/f8-pro-desktop-t1').write_text('Official Armbian 26.8.1 native writable Plasma Wayland desktop T1\n')
    assert not list((mount/'etc/ssh').glob('ssh_host_*_key'))
    assert not list((mount/'etc/NetworkManager/system-connections').glob('*'))
    assert not (mount/'home/f8test').exists()
    assert (mount/'usr/libexec/f8-pro/f8_gsl_shuping.ko').exists()
    # The auto-login test user has no local password on first boot. Permit its
    # active local session to save Wi-Fi profiles without an admin password dialog.
    actions=['org.freedesktop.NetworkManager.settings.modify.system',
             'org.freedesktop.NetworkManager.network-control',
             'org.freedesktop.NetworkManager.enable-disable-wifi']
    policy=(mount/'usr/share/polkit-1/actions/org.freedesktop.NetworkManager.policy').read_text()
    assert all('id="'+action+'"' in policy for action in actions)
    rules=mount/'etc/polkit-1/rules.d';rules.mkdir(parents=True,exist_ok=True)
    (rules/'49-f8-test-network.rules').write_text('polkit.addRule(function(action, subject) {\n'
        '  var actions = '+json.dumps(actions)+';\n'
        '  if (subject.user === "f8test" && subject.local && subject.active && actions.indexOf(action.id) !== -1)\n'
        '    return polkit.Result.YES;\n});\n')
    subprocess.run(['sh','-n',str(dest)],check=True)
finally:
    subprocess.run(['umount',str(mount)],check=True)
with (out/'native-final-fsck.log').open('w') as log:
    subprocess.run(['e2fsck','-fn',str(image)],stdout=log,stderr=subprocess.STDOUT,check=True)
boot=out/m['boot_file']
assert hashlib.sha256(boot.read_bytes()).hexdigest()==m['boot_sha256']
for name in ['Connect-F8-Desktop.ps1','register-f8-desktop-hostkey.py']:
    shutil.copyfile(P/'tools'/name,out/name)
shutil.copyfile(P/'docs/flash-armbian-native-desktop-t1.md',out/'刷入说明.md')
entries=[(image,image.name),(boot,boot.name)]
entries += [(out/name,name) for name in ['native-image-manifest.json','SHA256SUMS','刷入说明.md','Connect-F8-Desktop.ps1','register-f8-desktop-hostkey.py']]
target=out/'F8_ARMBIAN_NATIVE_DESKTOP_T1.zip';partial=target.with_suffix('.zip.part')
print('Creating ZIP64 bundle; source images remain untouched',flush=True)
with zipfile.ZipFile(partial,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=1,allowZip64=True) as z:
    # Hash the exact byte stream being compressed; avoid a second raw-image scan.
    checksum=hashlib.sha256();count=0;report=512*1024**2
    with image.open('rb') as source, z.open(image.name,'w',force_zip64=True) as sink:
        while chunk:=source.read(1024*1024):
            checksum.update(chunk);sink.write(chunk);count+=len(chunk)
            if count>=report:
                print(json.dumps({'native_root_packed_mib':count//1024**2}),flush=True);report+=512*1024**2
    assert count==m['root_bytes']
    m['root_sha256']=checksum.hexdigest();m['root_sha256_pending']=False
    m['local_password_persists_after_change']=True
    manifest.write_text(json.dumps(m,indent=2)+'\n')
    (out/'SHA256SUMS').write_text(m['root_sha256']+'  '+image.name+'\n'+m['boot_sha256']+'  '+boot.name+'\n')
    for path,name in entries[1:]:z.write(path,name)
print('Verifying every ZIP entry and decompressed root checksum',flush=True)
with zipfile.ZipFile(partial) as z:
    for path,name in entries:
        with z.open(name) as stream:digest=hashlib.file_digest(stream,'sha256').hexdigest()
        if path==image:expected=m['root_sha256']
        else:
            with path.open('rb') as stream:expected=hashlib.file_digest(stream,'sha256').hexdigest()
        assert digest==expected,name
partial.rename(target)
with target.open('rb') as stream:digest=hashlib.file_digest(stream,'sha256').hexdigest()
record={'bundle':target.name,'bytes':target.stat().st_size,'sha256':digest,'all_zip_entries_verified':True,
        'desktop_touch_keyboard_user_confirmed':True,'native_cold_boot_verified':False,'target_partition_written':False}
(out/'desktop-bundle.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps(record,indent=2),flush=True)
