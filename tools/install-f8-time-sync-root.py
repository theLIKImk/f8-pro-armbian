"""Install Chrony enablement for F8's custom systemd boot target."""
import argparse,json,os,subprocess
from pathlib import Path

def install(root,packages=False):
 root=Path(root).resolve();assert os.geteuid()==0 and (root/'etc/systemd/system/f8-desktop.target').is_file()
 prefix=[] if root==Path('/') else ['chroot',str(root)]
 if packages:subprocess.run(prefix+['apt-get','-y','--no-install-recommends','install','chrony'],check=True,env=dict(os.environ,DEBIAN_FRONTEND='noninteractive'),timeout=300)
 assert (root/'usr/lib/systemd/system/chrony.service').is_file(),'Install the chrony package first'
 target=root/'etc/systemd/system/f8-desktop.target';before=target.read_text()
 backup=root/'var/lib/f8-pro/backups/time-sync-before-r1';backup.mkdir(parents=True,exist_ok=True,mode=0o700)
 if not (backup/'f8-desktop.target').exists():(backup/'f8-desktop.target').write_text(before)
 lines=[]
 for line in before.splitlines():
  if line.startswith('Wants='):
   line='Wants='+' '.join(x for x in line[6:].split() if x not in ['systemd-timesyncd.service','chrony.service'])
  lines.append(line)
 target.write_text('\n'.join(lines)+'\n')
 # Enable/disable through timedatectl must govern both normal and custom boots.
 p=root/'etc/systemd/system/chrony.service.d/50-f8-desktop.conf';p.parent.mkdir(parents=True,exist_ok=True)
 p.write_text('# F8 custom boot target; extends the distribution Install section.\n[Install]\nWantedBy=f8-desktop.target\n');p.chmod(0o644)
 for unit in ['multi-user.target','f8-desktop.target']:
  p=root/f'etc/systemd/system/{unit}.wants/chrony.service';p.parent.mkdir(parents=True,exist_ok=True)
  if p.is_symlink():assert p.readlink().as_posix() in ['/usr/lib/systemd/system/chrony.service','/lib/systemd/system/chrony.service']
  else:
   assert not p.exists();p.symlink_to('/usr/lib/systemd/system/chrony.service')
 if root==Path('/'):
  subprocess.run(['systemctl','daemon-reload'],check=True)
  subprocess.run(['systemctl','enable','--now','chrony.service'],check=True,capture_output=True)
 return {'root':str(root),'provider':'chrony','enabled_targets':['multi-user.target','f8-desktop.target'],'vendor_time_sources_preserved':True}

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--install-packages',action='store_true');a=p.parse_args();print(json.dumps(install(a.root,a.install_packages)))
