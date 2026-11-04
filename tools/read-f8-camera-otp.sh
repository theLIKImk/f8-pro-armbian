#!/bin/sh
set -eu
python3 -I - <<'PY'
import fcntl,json,os,struct
from pathlib import Path
assert Path('/proc/sys/kernel/random/boot_id').read_text().strip()=='532eb6df-13ce-4e63-9645-24d4136d96b9'
out={}
for name,node in [('front','/dev/v4l-subdev2'),('back','/dev/v4l-subdev5')]:
    fd=os.open(node,os.O_RDWR|os.O_NONBLOCK)
    try:
        b=bytearray(5207);fcntl.ioctl(fd,0x945756c0,b,True)
        values=struct.unpack_from('<9I',b,176)
        out[name]={'awb':dict(zip(['flag','r','b','gr','gb','golden_r','golden_b','golden_gr','golden_gb'],values)),
         'lsc_flag':struct.unpack_from('<I',b,212)[0],
         'lsc_grid':struct.unpack_from('<3H',b,216),
         'lsc_resolution_table_size':struct.unpack_from('<3H',b,2534)}
    finally:os.close(fd)
print(json.dumps(out,indent=2))
PY
