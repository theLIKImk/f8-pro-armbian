"""Inventory/retain metadata only; actual Windows removal uses native PowerShell."""
from pathlib import Path
import json,os,shutil,time
P=Path(__file__).resolve().parents[1];R=P/'outputs';R=R.resolve()
A=P/'analysis/build-cleanup/20261102';A.mkdir(parents=True,exist_ok=True)
assert not (A/'windows-delete-result.json').exists(),'One-time cleanup already completed; preserve its audit'
keep={'f8-first-run-r1a','official-f8-camera-c4','official-f8-camera-c2','f8-cover-haptic-h2','extra-modules-6.1.115','official-f8-usb-u1-module'}
targets=[p for p in R.iterdir() if p.name!='armbian']+[p for p in (R/'armbian').iterdir() if p.name not in keep]
binary={'.img','.zip','.part','.squashfs','.gz','.xz','.zst','.deb','.ko','.so','.o','.a','.elf','.bin','.dtb','.itb','.cpio','.sig'}
rows=[];metadata=0
for p in targets:
 assert p.resolve().is_relative_to(R) and p.resolve()!=R
 files=[p] if p.is_file() else [Path(base)/n for base,dirs,names in os.walk(p,followlinks=False) for n in names]
 total=0
 for f in [p,*files]:
  if f.is_symlink() or (f.lstat().st_file_attributes & 0x400):raise RuntimeError('Reparse point requires separate handling: '+str(f))
 for f in files:
  size=f.stat().st_size;total+=size
  if size>10*1024**2 or f.suffix.lower() in binary:continue
  data=f.read_bytes()
  if b'\0' in data:continue
  try:data.decode('utf-8')
  except UnicodeDecodeError:continue
  dest=A/'retired-output-metadata'/f.relative_to(R);dest.parent.mkdir(parents=True,exist_ok=True)
  shutil.copyfile(f,dest);assert dest.read_bytes()==data;metadata+=1
 rows.append({'path':str(p),'relative':str(p.relative_to(R)),'logical_bytes':total,'files':len(files)})
plan={'root':str(R),'time':time.time(),'keep_armbian_directories':sorted(keep),'metadata_files_preserved':metadata,'targets':rows,'logical_bytes':sum(x['logical_bytes'] for x in rows),'source_documents_backups_untouched':True}
(A/'windows-delete-plan.json').write_text(json.dumps(plan,indent=2)+'\n')
print(json.dumps({'targets':len(rows),'logical_gib':round(plan['logical_bytes']/1024**3,2),'metadata_files_preserved':metadata,'plan':str(A/'windows-delete-plan.json')},indent=2))
