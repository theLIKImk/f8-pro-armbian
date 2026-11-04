"""Install the lunar calendar plugin and once-per-user defaults into a release root."""
import argparse,os,json,subprocess,shutil
from pathlib import Path
P=Path(__file__).resolve().parents[1]
PACKAGES=['plasma-calendar-addons','qdbus-qt6']
def install(root,packages=False):
 root=Path(root).resolve();assert os.geteuid()==0 and (root/'etc').is_dir()
 prefix=[] if root==Path('/') else ['chroot',str(root)]
 if packages:subprocess.run(prefix+['apt-get','-y','--no-install-recommends','install',*PACKAGES],check=True,env=dict(os.environ,DEBIAN_FRONTEND='noninteractive'),timeout=300)
 assert list(root.glob('usr/lib/*-linux-gnu/qt6/plugins/plasmacalendarplugins/alternatecalendar.so')),'Calendar addon is missing'
 assert (root/'usr/bin/qdbus6').is_file() and (root/'usr/bin/kwriteconfig6').is_file()
 for source,dest in [
  ('calendar-defaults.py','usr/libexec/f8-pro/calendar-defaults.py'),
  ('f8-calendar-defaults.desktop','etc/xdg/autostart/f8-calendar-defaults.desktop'),
  ('plasma_calendar_alternatecalendar','etc/skel/.config/plasma_calendar_alternatecalendar'),
  ('packages.txt','usr/share/f8-pro/calendar/packages.txt')]:
  p=root/dest;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((P/'armbian/calendar'/source).read_bytes().removeprefix(b'\xef\xbb\xbf'));p.chmod(0o644)
 return {'packages':PACKAGES,'calendarSystem':'Chinese','activation':'once per user via Plasma scripting','preserve_existing_plugins':True}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--install-packages',action='store_true');a=p.parse_args();print(json.dumps(install(a.root,a.install_packages)))
