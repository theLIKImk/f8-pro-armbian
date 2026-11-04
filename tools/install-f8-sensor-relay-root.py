"""Install the tested relay rootfs assets into a release root; never copy user calibration."""
from pathlib import Path
import argparse,json,os,hashlib,subprocess
P=Path(__file__).resolve().parents[1];O=P/'outputs/armbian/f8-sensor-relay-r2'
LINKS={'etc/systemd/system/f8-desktop.target.wants/f8-sensor-relay-hardware.service':'../f8-sensor-relay-hardware.service','etc/systemd/user/graphical-session.target.wants/f8-sensor-relay.service':'../f8-sensor-relay.service'}
def install(root):
 R=Path(root).resolve();assert os.geteuid()==0 and (R/'etc').is_dir()
 m=json.loads((O/'installation-manifest.json').read_text());files={}
 for name,v in m['files'].items():
  b=(O/'rootfs'/name).read_bytes();assert hashlib.sha256(b).hexdigest()==v['sha256']
  p=R/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b);p.chmod(v['mode']);files[name]=v['sha256']
 for name,target in LINKS.items():
  p=R/name;p.parent.mkdir(parents=True,exist_ok=True)
  if p.is_symlink():
   saved=p.readlink();actual=R/str(saved).lstrip('/') if saved.is_absolute() else p.parent/saved
   assert os.path.normpath(str(actual))==os.path.normpath(str(p.parent/target))
   if str(saved)!=target:p.unlink();p.symlink_to(target)
  elif p.exists():raise RuntimeError('Unexpected enable-link file: '+str(p))
  else:p.symlink_to(target)
 subprocess.run(['depmod','-b',str(R),'6.1.115-vendor-rk35xx'],check=True,capture_output=True)
 return {'files':files,'links':LINKS,'personal_calibration_copied':False}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--root',required=True);a=p.parse_args();print(json.dumps(install(a.root),indent=2))
