"""Preserve current board assets before deleting obsolete full staging roots."""
from pathlib import Path
import hashlib,json,os,stat,tarfile,io
P=Path(__file__).resolve().parents[1];R=Path('/var/tmp/f8-pro-armbian/release-r1/rootfs')
O=P/'vendor/f8-current-runtime-20261102';O.mkdir(exist_ok=True)
assert not (O/'manifest.json').exists()
selected={}
def collect(rel):
 p=R/rel
 if not p.exists() and not p.is_symlink():return
 selected[rel]=p
 if p.is_dir() and not p.is_symlink():
  for base,dirs,files in os.walk(p,followlinks=False):
   for name in dirs+files:
    f=Path(base)/name;selected[str(f.relative_to(R))]=f
for name in ['usr/local','usr/libexec/f8-pro','opt/f8-pro-camera','usr/lib/firmware/f8-pro','usr/lib/firmware/ap6275p','usr/lib/modules/6.1.115-vendor-rk35xx/extra','usr/share/alsa/ucm2/F8-PRO','usr/share/wireplumber/wireplumber.conf.d/50-f8-ucm.conf','var/lib/alsa/asound.state','etc/modules-load.d','etc/modprobe.d','etc/udev/rules.d','etc/udev/hwdb.d','etc/wireplumber','etc/systemd/system/sddm.service.d','etc/skel']:
 collect(name)
for pat in ['etc/systemd/system/f8*','usr/share/applications/f8-*.desktop']:
 for p in R.glob(pat):collect(str(p.relative_to(R)))
for name in ['usr/libexec/f8-pro/live-setup.sh','usr/libexec/f8-pro/desktop-session-record.sh','usr/libexec/f8-pro/graphics-report','etc/systemd/system/f8-live-ssh.service']:
 selected.pop(name,None)
overrides={}
for name in ['first-run.py','first-run-apply.py','setup-cleanup.py','root-grow-r1a.py']:
 overrides['usr/local/lib/f8-pro/'+name]=((P/'armbian/first-run'/name).read_bytes(),0o755)
for name in ['f8-setup-cleanup.service','f8-setup-cleanup.timer','f8-root-grow-r1a.service']:
 overrides['etc/systemd/system/'+name]=((P/'armbian/first-run'/name).read_bytes(),0o644)
overrides['usr/libexec/f8-pro/native-prepare.sh']=((P/'armbian/first-run/native-prepare.sh').read_bytes(),0o755)
for source,target in [('f8-first-run.desktop','etc/xdg/autostart/f8-first-run.desktop'),('f8-guide.desktop','usr/share/applications/f8-guide.desktop')]:
 overrides[target]=((P/'armbian/first-run'/source).read_bytes(),0o644)
for name in overrides:selected.pop(name,None)
manifest={};archive=O/'runtime-overlay.tar.gz'
with tarfile.open(archive,'w:gz',dereference=False,compresslevel=6) as tar:
 for name,p in sorted(selected.items()):
  assert not name.startswith(('home/','root/','etc/netplan/','etc/NetworkManager/'))
  assert 'authorized_keys' not in name and 'ssh_host_' not in name
  tar.add(p,arcname=name,recursive=False)
  if p.is_file() and not p.is_symlink():
   data=p.read_bytes();assert b'-----BEGIN OPENSSH PRIVATE KEY-----' not in data
   manifest[name]={'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data)}
  elif p.is_symlink():manifest[name]={'link':os.readlink(p)}
 for name,(data,mode) in sorted(overrides.items()):
  ti=tarfile.TarInfo(name);ti.size=len(data);ti.mode=mode;ti.uid=0;ti.gid=0;tar.addfile(ti,io.BytesIO(data))
  manifest[name]={'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data),'updated_from_project_source':True}
for name in ['usr/libexec/f8-pro/f8_gsl_shuping.ko','usr/libexec/f8-pro/f8_otg_vbus_u2.ko','usr/local/lib/f8-pro/libf8-camera-relay-view.so','usr/local/lib/f8-pro/camera-preview.py']:
 assert name in manifest,name
with archive.open('rb') as f:digest=hashlib.file_digest(f,'sha256').hexdigest()
# Verify archive bytes against every retained regular file, without extracting.
with tarfile.open(archive,'r:gz') as tar:
 for name,item in manifest.items():
  if 'sha256' in item:assert hashlib.file_digest(tar.extractfile(name),'sha256').hexdigest()==item['sha256'],name
report={'archive':archive.name,'bytes':archive.stat().st_size,'sha256':digest,'files':manifest,'not_a_complete_rootfs':True,'no_homes_netplan_networkmanager_or_ssh_keys_included':True,'cleanup_and_account_fix_sources_included':True}
(O/'manifest.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'archive':str(archive),'bytes':archive.stat().st_size,'entries':len(manifest),'sha256':digest},indent=2))
