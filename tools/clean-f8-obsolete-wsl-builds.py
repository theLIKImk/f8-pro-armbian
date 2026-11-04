"""Delete allowlisted project build workspaces, never source trees/backups."""
from pathlib import Path
import hashlib,json,os,shutil,subprocess,time
P=Path(__file__).resolve().parents[1];A=P/'analysis/build-cleanup/20261102';A.mkdir(exist_ok=True)
assert not (A/'wsl-delete-result.json').exists(),'One-time cleanup already completed; preserve its audit'
kit=P/'vendor/f8-current-runtime-20261102';manifest=json.loads((kit/'manifest.json').read_text())
with (kit/manifest['archive']).open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==manifest['sha256']
bases={Path('/var/tmp/f8-pro-armbian'):{'private-backups','f8-official-armbian-26.8.1','official-kernel','official-host-tools','host-tools','initramfs-tools','linux-rockchip-config','camera-aiq-audit','feedbackd-0.8.9-source','feedbackd-0.8.9-audit','plasma-keyboard-6.6.6','kamoso-source-25.12.3','iio-proxy-source-3.8','vendor-camera-source-audit','touch-reference','browser-camera-156','post-wizard-likimk'},Path('/var/tmp/f8-pro-archlinux-20261027'):{'backups','evidence','private-keys','rootfs-vendor-staging'}}
mounts=[Path(x.split()[4]) for x in Path('/proc/self/mountinfo').read_text().splitlines()]
targets=[]
for base,keep in bases.items():
 assert base.resolve()==base and base.parent==Path('/var/tmp')
 for p in base.iterdir():
  if p.name in keep or not p.is_dir():continue
  assert not p.is_symlink() and p.resolve().parent==base
  assert not any(m==p or m.is_relative_to(p) for m in mounts),'Mounted candidate '+str(p)
  targets.append(p)
# No live compiler, archiver, or process whose working directory is being removed.
for proc in Path('/proc').iterdir():
 if not proc.name.isdigit() or int(proc.name)==os.getpid():continue
 try:
  cwd=(proc/'cwd').resolve();args=(proc/'cmdline').read_bytes().split(b'\0')
 except OSError:continue
 assert not any(cwd==p or cwd.is_relative_to(p) for p in targets),'Busy workspace '+str(cwd)
 if args and Path(args[0].decode(errors='replace')).name in {'make','mke2fs','mkfs.ext4','rsync'}:
  raise AssertionError('Build process still running; do not clean')
before=os.statvfs('/');free_before=before.f_bavail*before.f_frsize
records=[];metadata_count=0
for target in targets:
 keepfiles=set()
 for pattern in ['*.json','*.log','*.txt','*.its','*.config','.config','.config.old']:
  keepfiles.update(target.glob(pattern))
 for f in sorted(keepfiles):
  if not f.is_file() or f.is_symlink() or f.stat().st_size>10*1024**2:continue
  data=f.read_bytes()
  if b'\0' in data:continue
  try:data.decode('utf-8')
  except UnicodeDecodeError:continue
  dest=A/'retired-wsl-metadata'/target.parent.name/target.name/f.name;dest.parent.mkdir(parents=True,exist_ok=True)
  dest.write_bytes(data);assert dest.read_bytes()==data;metadata_count+=1
 records.append({'path':str(target)})
(A/'wsl-delete-plan.json').write_text(json.dumps({'targets':records,'kept':{str(k):sorted(v) for k,v in bases.items()},'metadata_preserved':metadata_count,'free_before':free_before},indent=2)+'\n')
for target in targets:
 assert target.resolve().parent in bases and not target.is_symlink()
 shutil.rmtree(target)
 assert not target.exists()
 print('Removed '+str(target),flush=True)
for name in ['f8-camera-relay-view.so','f8-gst-buffer-trial.so','f8-vibrate']:
 p=Path('/var/tmp')/name
 if p.is_file() and not p.is_symlink():p.unlink()
# Compiled probes inside retained source audits are disposable; source stays.
audit=Path('/var/tmp/f8-pro-armbian/camera-aiq-audit')
for p in audit.rglob('*'):
 if p.is_file() and not p.is_symlink() and p.suffix in {'.so','.o','.a'}:p.unlink()
after=os.statvfs('/');free_after=after.f_bavail*after.f_frsize
result={'completed':True,'deleted_directories':records,'free_before':free_before,'free_after':free_after,'freed_bytes':free_after-free_before,'metadata_preserved':metadata_count,'runtime_retention_sha256':manifest['sha256'],'private_backups_keys_and_source_kept':True,'tablet_touched':False,'wsl_vhd_compacted':False}
(A/'wsl-delete-result.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'completed':True,'directories':len(targets),'freed_gib':round((free_after-free_before)/1024**3,2)},indent=2),flush=True)
