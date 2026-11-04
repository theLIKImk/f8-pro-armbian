"""Reproduce C4 into new directories and compare bytes; never touches a device.

The original builder and completed C4 artifacts remain unchanged. The archived
ITS removes a dependency on the transient WSL camera-c2 build directory.
"""
import argparse,hashlib,json,re
from pathlib import Path
P=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--name',default='camera-c4-repro-verified');args=parser.parse_args()
assert re.fullmatch(r'camera-c4-repro-[a-z0-9-]{1,40}',args.name),'Use a new isolated reproduction name'
builder=P/'tools/build-f8-camera-c4.py'
source=builder.read_text()
replacements={
 "P/'outputs/armbian/official-f8-camera-c4'":f"P/'outputs/armbian/official-f8-{args.name}'",
 "Path('/var/tmp/f8-pro-armbian/camera-c4')":f"Path('/var/tmp/f8-pro-armbian/{args.name}')",
 "'BOOT_ONLY_ARMBIAN_CAMERA_C4.img'":"'BOOT_ONLY_ARMBIAN_CAMERA_C4_REPRO.img'",
}
for old,new in replacements.items():
    assert source.count(old)==1,('Builder changed; review the reproduction wrapper',old)
    source=source.replace(old,new)
exec(compile(source,str(builder),'exec'),{'__name__':'__main__','__file__':str(builder)})
original=P/'outputs/armbian/official-f8-camera-c4/BOOT_ONLY_ARMBIAN_CAMERA_C4.img'
repro=P/f'outputs/armbian/official-f8-{args.name}/BOOT_ONLY_ARMBIAN_CAMERA_C4_REPRO.img'
assert original.read_bytes()==repro.read_bytes(),'Reproduction differs: do not flash; inspect differences'
report={'result':'PASS','byte_identical_to_verified_c4':True,'bytes':repro.stat().st_size,
 'sha256':hashlib.sha256(repro.read_bytes()).hexdigest(),'device_accessed':False,
 'original_image_modified':False,'original_preflight_modified':False}
(repro.parent/'reproduction-check.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
