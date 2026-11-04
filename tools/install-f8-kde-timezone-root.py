"""Ensure KDE's timezone selector can load with --no-install-recommends builds."""
import argparse,json,os,subprocess
from pathlib import Path
PACKAGES=['qml6-module-qtlocation','qml6-module-qtpositioning','qt6-location-plugins','plasma-workspace-data']
def install(root,packages=False):
 root=Path(root).resolve();assert os.geteuid()==0 and (root/'etc').is_dir()
 prefix=[] if root==Path('/') else ['chroot',str(root)]
 if packages:subprocess.run(prefix+['apt-get','-y','--no-install-recommends','install',*PACKAGES],check=True,env=dict(os.environ,DEBIAN_FRONTEND='noninteractive'),timeout=300)
 result={}
 for name,pattern in {
  'location_qml':'usr/lib/*-linux-gnu/qt6/qml/QtLocation/qmldir',
  'positioning_qml':'usr/lib/*-linux-gnu/qt6/qml/QtPositioning/qmldir',
  'osm_plugin':'usr/lib/*-linux-gnu/qt6/plugins/geoservices/libqtgeoservices_osm.so',
 }.items():
  paths=[p for p in root.glob(pattern) if p.is_file()];assert paths,('Missing timezone dependency',name);result[name]=str(paths[0].relative_to(root))
 p=root/'usr/share/timezonefiles/timezones.json';assert p.is_file() and p.stat().st_size>0,'Missing offline timezone geometry'
 result['timezone_geometry']=str(p.relative_to(root))
 result['packages']=PACKAGES
 return result
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--install-packages',action='store_true');a=p.parse_args();print(json.dumps(install(a.root,a.install_packages)))
