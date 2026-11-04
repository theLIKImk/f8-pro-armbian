"""Read only the factory Ubuntu image; extract camera ELF for isolated ABI audit."""
import hashlib,json
from pathlib import Path
from inspect_images import Package,Ext4
P=Path(__file__).resolve().parents[1]
source=P.parent/'update-UBUNTU20.04.img'
out=P/'analysis/armbian/camera/factory-aiq';out.mkdir(exist_ok=True)
pkg=Package(source);fs=Ext4(pkg,'rootfs');report={}
for directory in ['/usr/lib','/usr/lib/aarch64-linux-gnu','/usr/bin','/usr/lib64','/lib']:
    try:entries=list(fs.ls(fs.lookup(directory)))
    except (StopIteration,ValueError):continue
    for name,ino,kind in entries:
        if 'rkaiq' not in name:continue
        body=fs.content(ino)
        if body.startswith(b'\x7fELF'):
            target=out/(directory.strip('/').replace('/','_')+'_'+name)
            assert not target.exists();target.write_bytes(body)
            report[directory+'/'+name]={'file':target.name,'bytes':len(body),'sha256':hashlib.sha256(body).hexdigest()}
        else:report[directory+'/'+name]={'kind':kind,'link_or_data':body[:128].decode(errors='replace')}
(out/'manifest.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
