"""Show only packaging process and large image/archive progress, no user data."""
import json
from pathlib import Path
P=Path(__file__).resolve().parents[1]
for proc in Path('/proc').iterdir():
    if not proc.name.isdigit():continue
    try:
        args=(proc/'cmdline').read_bytes().split(b'\0')
        scripts=[Path(x.decode()).name for x in args if x.endswith(b'.py')]
        if not any(x in {'pack-f8-native-desktop-t1.py','build-f8-private-rollback.py','finalize-f8-desktop-t1.py','export-f8-private-rollback.py'} for x in scripts):continue
        positions=[]
        for fd in (proc/'fd').iterdir():
            try:
                path=fd.resolve()
                if not str(path).endswith(('.img','.gz','.zip.part')):continue
                info=(proc/'fdinfo'/fd.name).read_text()
                pos=int(next(x.split()[1] for x in info.splitlines() if x.startswith('pos:')))
                positions.append({'file':path.name,'position_mib':pos//1024**2,'size_mib':path.stat().st_size//1024**2})
            except (OSError,StopIteration):pass
        print(json.dumps({'pid':proc.name,'scripts':scripts,'positions':positions}))
    except OSError:pass
for filename in ['native-image-manifest.json','desktop-bundle.json']:
    print(filename,(P/'outputs/armbian/official-f8-desktop-t1'/filename).exists())
print('rollback verified',Path('/var/tmp/f8-pro-armbian/private-backups/20261030-original-root/rollback-manifest.json').exists())
for path in [Path('/var/tmp/f8-pro-armbian/desktop-t1/native-image/ROOTFS_ARMBIAN_DESKTOP_T1.ext4.img'),
             Path('/var/tmp/f8-pro-armbian/private-backups/20261030-original-root/ROOTFS_ORIGINAL_ROLLBACK.ext4.img')]:
    if path.exists():
        s=path.stat();print(json.dumps({'image':path.name,'allocated_mib':s.st_blocks*512//1024**2,'logical_mib':s.st_size//1024**2}))
