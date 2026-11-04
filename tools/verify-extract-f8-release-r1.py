"""Native Windows ZIP verification plus sparse raw files for RKDevTool."""
import ctypes,hashlib,json,msvcrt,os,shutil,zipfile,sys,time
from pathlib import Path
P=Path(__file__).resolve().parents[1];O=P/'outputs/armbian/f8-armbian-r1'
if '--wait' in sys.argv:
 for _ in range(900):
  if (O/'zip-ready.json').exists():break
  time.sleep(2)
assert (O/'zip-ready.json').exists(),'Wait for the completed ZIP writer'
m=json.loads((O/'image-manifest.json').read_text())
part=O/'F8_ARMBIAN_R1_TEST.zip.part';target=O/'F8_ARMBIAN_R1_TEST.zip'
assert not target.exists() and not (O/'bundle.json').exists()
dest=O/'flash-files';dest.mkdir(exist_ok=True)
assert shutil.disk_usage(dest).free>16*1024**3
io=ctypes.WinDLL('kernel32',use_last_error=True).DeviceIoControl
io.argtypes=[ctypes.c_void_p,ctypes.c_uint32,ctypes.c_void_p,ctypes.c_uint32,ctypes.c_void_p,ctypes.c_uint32,ctypes.POINTER(ctypes.c_uint32),ctypes.c_void_p];io.restype=ctypes.c_int
raw={m['root_file']:m['root_sha256'],m['boot_file']:m['boot_sha256']}
names=[*raw,'image-manifest.json','first-run-native-test.json','root-integration.json','刷入与首次设置.md','SHA256SUMS']
files=[]
with zipfile.ZipFile(part) as z:
 assert sorted(z.namelist())==sorted(names)
 for name in names:
  h=hashlib.sha256();count=0
  if name in raw:
   output=dest/name;partial=output.with_suffix(output.suffix+'.part');assert not output.exists() and not partial.exists()
   with z.open(name) as source,partial.open('xb') as sink:
    returned=ctypes.c_uint32();sparse=bool(io(msvcrt.get_osfhandle(sink.fileno()),0x900C4,None,0,None,0,ctypes.byref(returned),None))
    while chunk:=source.read(4*1024**2):
     h.update(chunk);count+=len(chunk)
     if sparse and chunk.count(0)==len(chunk):sink.seek(len(chunk),os.SEEK_CUR)
     else:sink.write(chunk)
    sink.truncate(count);sink.flush();os.fsync(sink.fileno())
   assert h.hexdigest()==raw[name] and count==z.getinfo(name).file_size
   partial.rename(output);files.append({'file':str(output),'bytes':count,'sha256':h.hexdigest(),'ntfs_sparse':sparse})
  else:
   with z.open(name) as source:h=hashlib.file_digest(source,'sha256')
   assert h.hexdigest()==hashlib.sha256((O/name).read_bytes()).hexdigest(),name
  print('Verified '+name,flush=True)
part.rename(target)
with target.open('rb') as f:digest=hashlib.file_digest(f,'sha256').hexdigest()
(dest/'flash-files.json').write_text(json.dumps({'images':files,'target_partition_written':False},indent=2)+'\n')
(O/'bundle.json').write_text(json.dumps({'bundle':target.name,'bytes':target.stat().st_size,'sha256':digest,'all_zip_entries_verified':True,'windows_raw_flash_files_extracted':True,'target_partition_written':False,'packaged_cold_boot_verified':False},indent=2)+'\n')
print('R1 bundle and raw files verified; no partition written',flush=True)
