"""Install tested F8 sensor fusion/viewer assets and the verified EM30918 module."""
from pathlib import Path
import argparse,hashlib,json,os,subprocess
P=Path(__file__).resolve().parents[1]
NAMES=['gyro_stabilizer.py','sensor-monitor.py','sensor_examples.py','motion_examples_math.py','sensor_fusion.py','fusion_view.py','compass-view.py']
def install(root):
 root=Path(root).resolve();assert os.geteuid()==0 and (root/'etc').is_dir()
 source=P/'outputs/armbian/f8-em30918-r1';manifest=json.loads((source/'module-check.json').read_text())
 assert manifest['all_import_crcs_verified_against_actual_image']
 assert hashlib.sha256((source/'f8_em30918.ko').read_bytes()).hexdigest()==manifest['sha256']
 files={}
 def put(name,data,mode=0o644):
  p=root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data);p.chmod(mode);files[name]=hashlib.sha256(data).hexdigest()
 for name in NAMES:put('usr/local/lib/f8-pro/'+name,(P/'armbian/motion'/name).read_bytes().removeprefix(b'\xef\xbb\xbf'),0o755)
 put('usr/lib/modules/6.1.115-vendor-rk35xx/extra/f8-pro/f8_em30918.ko',(source/'f8_em30918.ko').read_bytes())
 put('usr/share/f8-pro/sensors-f2/em30918-module.json',(source/'module-check.json').read_bytes())
 for name,dest in [('optical-start.py','usr/libexec/f8-pro/optical-start.py'),('f8-optical.service','etc/systemd/system/f8-optical.service')]:put(dest,(P/'armbian/motion'/name).read_bytes().removeprefix(b'\xef\xbb\xbf'))
 link=root/'etc/systemd/system/f8-desktop.target.wants/f8-optical.service';link.parent.mkdir(parents=True,exist_ok=True)
 if link.is_symlink():
  assert link.readlink().as_posix() in ['../f8-optical.service','/etc/systemd/system/f8-optical.service']
  if link.readlink().as_posix()!='../f8-optical.service':link.unlink();link.symlink_to('../f8-optical.service')
 elif not link.exists():link.symlink_to('../f8-optical.service')
 else:raise RuntimeError('Unexpected service enable path')
 subprocess.run(['depmod','-b',str(root),'6.1.115-vendor-rk35xx'],check=True,capture_output=True)
 return {'files':files,'heading_offset_deg':180,'module_verified':True,'personal_calibration_copied':False}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--root',required=True);a=p.parse_args();print(json.dumps(install(a.root),indent=2))
