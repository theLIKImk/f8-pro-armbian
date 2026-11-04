"""Package the accepted F8 sensor viewer/fusion and verified optical kernel module."""
from pathlib import Path
import base64,hashlib,json,tarfile,shutil,py_compile
P=Path(__file__).resolve().parents[1];A=P/'armbian/motion';O=P/'outputs/armbian/f8-sensors-f2';R=O/'rootfs';R.mkdir(parents=True,exist_ok=True)
roles={}
for name in ['gyro_stabilizer.py','sensor-monitor.py','sensor_examples.py','motion_examples_math.py','sensor_fusion.py','fusion_view.py','compass-view.py']:roles['usr/local/lib/f8-pro/'+name]=(A/name,0o755)
roles.update({
 'usr/libexec/f8-pro/optical-start.py':(A/'optical-start.py',0o644),
 'etc/systemd/system/f8-optical.service':(A/'f8-optical.service',0o644),
 'usr/lib/modules/6.1.115-vendor-rk35xx/extra/f8-pro/f8_em30918.ko':(P/'outputs/armbian/f8-em30918-r1/f8_em30918.ko',0o644),
 'usr/share/f8-pro/sensors-f2/em30918-module.json':(P/'outputs/armbian/f8-em30918-r1/module-check.json',0o644)})
files={}
for target,(source,mode) in roles.items():
 b=source.read_bytes().removeprefix(b'\xef\xbb\xbf');dest=R/target;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(b)
 if source.suffix=='.py':compile(b,str(source),'exec')
 files[target]={'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b),'mode':mode,'source':str(source.relative_to(P)).replace('\\','/')}
links={'etc/systemd/system/f8-desktop.target.wants/f8-optical.service':'../f8-optical.service'}
manifest={'version':'F2','date':'2026-11-03','files':files,'links':links,'heading_offset_deg':180,'kernel':'6.1.115-vendor-rk35xx','optical_module':json.loads((P/'outputs/armbian/f8-em30918-r1/module-check.json').read_text()),'calibrations_packaged':False,'shared_fusion_output':'/run/user/UID/f8-sensor-fusion.json; only while observation app runs','optical_units':'raw ADC counts; lux/cm not calibrated','boot_image_changed':False}
(O/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
shutil.copyfile(A/'f8_em30918.c',O/'f8_em30918.c')
def permissions(info):
 info.uid=info.gid=0;info.uname=info.gname='root'
 info.mode=0o755 if info.isdir() else files.get(info.name.removeprefix('rootfs/'),{}).get('mode',0o644)
 return info
with tarfile.open(O/'f8-sensors-f2.tar.gz','w:gz') as t:
 t.add(R,arcname='rootfs',filter=permissions);t.add(O/'manifest.json',arcname='manifest.json',filter=permissions);t.add(O/'f8_em30918.c',arcname='source/f8_em30918.c',filter=permissions)
 for name,target in links.items():
  i=tarfile.TarInfo('rootfs/'+name);i.type=tarfile.SYMTYPE;i.linkname=target;i.mode=0o777;t.addfile(i)
with tarfile.open(O/'f8-sensors-f2.tar.gz') as t:
 for name,v in files.items():
  i=t.getmember('rootfs/'+name);assert i.mode==v['mode'];assert hashlib.sha256(t.extractfile(i).read()).hexdigest()==v['sha256']
print(json.dumps({'files':len(files),'bytes':(O/'f8-sensors-f2.tar.gz').stat().st_size,'sha256':hashlib.sha256((O/'f8-sensors-f2.tar.gz').read_bytes()).hexdigest()}))
