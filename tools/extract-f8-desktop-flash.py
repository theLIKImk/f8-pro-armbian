"""Extract verified raw flash images on Windows, preserving zero ranges as holes."""
import ctypes
import hashlib
import json
import msvcrt
import os
from pathlib import Path
import shutil
import zipfile
P=Path(__file__).resolve().parents[1]
out=P/'outputs/armbian/official-f8-desktop-t1'
bundle=json.loads((out/'desktop-bundle.json').read_text());assert bundle['all_zip_entries_verified']
m=json.loads((out/'native-image-manifest.json').read_text())
dest=out/'flash-files';dest.mkdir(exist_ok=True)
assert not (dest/'flash-files.json').exists()
assert shutil.disk_usage(dest).free>15*1024**3
io=ctypes.WinDLL('kernel32',use_last_error=True).DeviceIoControl
io.argtypes=[ctypes.c_void_p,ctypes.c_uint32,ctypes.c_void_p,ctypes.c_uint32,ctypes.c_void_p,ctypes.c_uint32,ctypes.POINTER(ctypes.c_uint32),ctypes.c_void_p]
io.restype=ctypes.c_int
result=[]
with zipfile.ZipFile(out/bundle['bundle']) as z:
    for name,expected in [('ROOTFS_ARMBIAN_DESKTOP_T1.ext4.img',m['root_sha256']),(m['boot_file'],m['boot_sha256'])]:
        target=dest/name;part=target.with_suffix(target.suffix+'.part')
        assert not target.exists() and not part.exists()
        digest=hashlib.sha256();count=0;report=1024**3
        with part.open('xb') as sink,z.open(name) as source:
            returned=ctypes.c_uint32()
            sparse=bool(io(msvcrt.get_osfhandle(sink.fileno()),0x900C4,None,0,None,0,ctypes.byref(returned),None))
            while chunk:=source.read(4*1024**2):
                digest.update(chunk);count+=len(chunk)
                if sparse and chunk.count(0)==len(chunk):sink.seek(len(chunk),os.SEEK_CUR)
                else:sink.write(chunk)
                if count>=report:
                    print(json.dumps({'image':name,'extracted_mib':count//1024**2}),flush=True);report+=1024**3
            sink.truncate(count);sink.flush();os.fsync(sink.fileno())
        assert count==z.getinfo(name).file_size and digest.hexdigest()==expected
        part.rename(target)
        result.append({'file':str(target),'bytes':count,'sha256':expected,'ntfs_sparse':sparse})
(dest/'flash-files.json').write_text(json.dumps({'images':result,'target_partition_written':False},indent=2)+'\n')
print('Raw Windows flash images ready; tablet partitions unchanged',flush=True)
