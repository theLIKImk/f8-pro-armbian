"""Build the current incremental package and synchronize rootfs-overlay."""
from pathlib import Path
import json,hashlib,tarfile,shutil,subprocess,sys
P=Path(__file__).resolve().parents[1];O=P/'outputs/armbian/f8-sensor-relay-r2';R=O/'rootfs'
subprocess.run([sys.executable,str(P/'tools/prepare-f8-sensor-relay.py')],check=True)
sys.path.insert(0,str(P/'tools'))
from importlib.util import spec_from_file_location,module_from_spec
spec=spec_from_file_location('relay_installer',P/'tools/install-f8-sensor-relay-root.py');module=module_from_spec(spec);spec.loader.exec_module(module)
m=json.loads((O/'installation-manifest.json').read_text());m.update(revision='R2',date='2026-11-03',links=module.LINKS,physical_magnetometer_hz=2.5,publish_target_hz=20,ambient_units='raw counts; no lux calibration',browser_extra_classes_enabled_by_default=False,browser_pose_transport='private CDP pipe with live fused quaternions',codertools_render_fix='host/path scoped CSS matrix; sensor values unchanged')
(O/'installation-manifest.json').write_text(json.dumps(m,indent=2)+'\n')
for name,v in m['files'].items():
 b=(R/name).read_bytes();assert hashlib.sha256(b).hexdigest()==v['sha256'];dest=P/'armbian/rootfs-overlay'/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(b)
for srcname in ['f8_sensor_relay.c','sensor-relay.py','brightness_policy.py','browser_pose_bridge.py','browser_pose_math.py','codertools-motion-fix.js']:
 shutil.copyfile(P/'armbian/sensor-relay'/srcname,O/srcname)
shutil.copyfile(P/'outputs/armbian/f8-sensor-relay-r1/module-check.json',O/'module-check.json')
archive=O/'f8-sensor-relay-r2.tar.gz'
def modes(i):
 i.uid=i.gid=0;i.uname=i.gname='root';i.mode=0o755 if i.isdir() else m['files'].get(i.name.removeprefix('rootfs/'),{}).get('mode',0o644);return i
with tarfile.open(archive,'w:gz') as t:
 t.add(R,arcname='rootfs',filter=modes);t.add(O/'installation-manifest.json',arcname='installation-manifest.json',filter=modes)
 for n in ['f8_sensor_relay.c','sensor-relay.py','brightness_policy.py','browser_pose_bridge.py','browser_pose_math.py','codertools-motion-fix.js']:t.add(O/n,arcname='source/'+n,filter=modes)
 for n,target in module.LINKS.items():
  i=tarfile.TarInfo('rootfs/'+n);i.type=tarfile.SYMTYPE;i.linkname=target;i.mode=0o777;t.addfile(i)
with tarfile.open(archive) as t:
 for name,v in m['files'].items():
  i=t.getmember('rootfs/'+name);assert i.mode==v['mode'];assert hashlib.sha256(t.extractfile(i).read()).hexdigest()==v['sha256']
print(json.dumps({'files':len(m['files']),'archive_bytes':archive.stat().st_size,'archive_sha256':hashlib.sha256(archive.read_bytes()).hexdigest()}))
