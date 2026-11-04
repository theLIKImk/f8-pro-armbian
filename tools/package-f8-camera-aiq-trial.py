"""Package only isolated ISP30 server/library and exact board IQ files, no deb install."""
import hashlib,io,json,tarfile
from pathlib import Path
P=Path(__file__).resolve().parents[1]
vendor=Path('/var/tmp/f8-pro-armbian/camera-aiq-audit/seeed')
factory=Path('/var/tmp/f8-pro-archlinux-20261027/rootfs-vendor-staging/etc/iqfiles')
out=P/'outputs/armbian/camera-aiq-c4-trial';out.mkdir(exist_ok=True)
target=out/'aiq-trial.tar.gz';assert not target.exists()
files={'bin/rkaiq_3A_server':vendor/'usr/bin/rkaiq_3A_server','lib/librkaiq.so':vendor/'usr/lib/librkaiq.so'}
for name in ['gc5035_XHG-RKX11F-V5_HR232H65.json','ov8858_HS5885-BNSM1018-V01_default.json']:
    files['iqfiles/'+name]=factory/name
manifest={'source_url':'https://github.com/Seeed-Studio/seeed_armbian_extension/releases/download/v1.0/camera_engine_rkaiq_rk3588_arm64_with_service.deb',
 'deb_sha256':hashlib.sha256(Path('/var/tmp/f8-pro-armbian/camera-aiq-audit/seeed-rk3588.deb').read_bytes()).hexdigest(),
 'aiq_version':'6.0x8.0 (2024-09-13)','target':'ISP30/RK3588','files':{},'deb_maintainer_scripts_executed':False,
 'global_library_replacement':False,'factory_iq_used_without_modification':True}
with tarfile.open(target,'w:gz') as tar:
    for name,path in files.items():
        data=path.read_bytes();mode=0o755 if name.startswith('bin/') else 0o644
        manifest['files'][name]={'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'mode':mode}
        info=tarfile.TarInfo(name);info.size=len(data);info.mode=mode;tar.addfile(info,io.BytesIO(data))
    data=(json.dumps(manifest,indent=2)+'\n').encode();info=tarfile.TarInfo('manifest.json');info.size=len(data);info.mode=0o644;tar.addfile(info,io.BytesIO(data))
(out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps({'file':str(target),'bytes':target.stat().st_size,'sha256':hashlib.sha256(target.read_bytes()).hexdigest()},indent=2))
