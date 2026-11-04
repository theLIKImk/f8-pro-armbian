"""Install the F8 Fcitx5 artifact into a live system or an explicit release root."""
import argparse,hashlib,json,os,pwd,shutil,subprocess,time,configparser
from pathlib import Path

def install(root,package,user=None,install_packages=False):
 root=Path(root).resolve();package=Path(package).resolve();manifest=json.loads((package/'manifest.json').read_text())
 assert os.geteuid()==0 and (root/'etc').is_dir()
 def command(args,check=True,**kw):return subprocess.run(args,check=check,capture_output=True,text=True,timeout=kw.pop('timeout',15),**kw)
 prefix=[] if root==Path('/') else ['chroot',str(root)]
 if install_packages:command(prefix+['apt-get','-y','--no-install-recommends','install',*manifest['packages']],env=dict(os.environ,DEBIAN_FRONTEND='noninteractive'),timeout=600)
 versions=command(prefix+['dpkg-query','-W','-f=${binary:Package} ${db:Status-Abbrev} ${Version}\n',*manifest['packages']]).stdout
 assert all(' ii ' in line for line in versions.splitlines()),versions
 backup=root/'var/lib/f8-pro/backups/fcitx5-before-r1';backup.mkdir(parents=True,exist_ok=True,mode=0o700)
 def preserve(p):
  if p.is_file():
   target=backup/p.relative_to(root)
   if not target.exists():target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,target)
 for name,info in manifest['files'].items():
  assert info['mode']&0o022==0,name
  rel=Path(name);assert not rel.is_absolute() and '..' not in rel.parts
  src=package/'rootfs'/rel;assert hashlib.sha256(src.read_bytes()).hexdigest()==info['sha256'],name
 for name,info in manifest['files'].items():
  p=root/name;preserve(p);p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(package/'rootfs'/name,p);p.chmod(info['mode'])
 for name,target in manifest['links'].items():
  p=root/name;p.parent.mkdir(parents=True,exist_ok=True)
  if p.is_symlink():p.unlink()
  assert not p.exists();p.symlink_to(target)
 p=root/'usr/share/f8-pro/fcitx5/manifest.json';p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(manifest,indent=2))
 command(prefix+['fc-cache','-f','/usr/share/fonts/truetype/f8-pro'])
 for name in ['fcitx5-osk','fcitx5-osk-kwin-launcher','fcitx5-osk-key-helper']:
  dep=command(prefix+['ldd','/usr/bin/'+name]);assert 'not found' not in dep.stdout,dep.stdout
 result={'versions':versions,'files':len(manifest['files']),'source_commit':manifest['source_commit'],'backup':str(backup)}
 if user:
  assert root==Path('/')
  account=pwd.getpwnam(user);uid=account.pw_uid;home=Path(account.pw_dir)
  u=['runuser','-u',user,'--','env',f'XDG_RUNTIME_DIR=/run/user/{uid}',f'DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/{uid}/bus']
  env_out=command(u+['systemctl','--user','show-environment']).stdout
  session={k:v for line in env_out.splitlines() if '=' in line for k,v in [line.split('=',1)] if k in ['DISPLAY','WAYLAND_DISPLAY','XAUTHORITY','XDG_SESSION_TYPE']}
  # Copy only the input defaults, preserving unrelated per-user desktop settings.
  for name in ['.config/fcitx5/profile','.config/fcitx5/config','.config/fcitx5-osk/config.toml','.config/environment.d/60-f8-fcitx5.conf','.config/plasma-workspace/env/f8-fcitx5.sh','.config/autostart/org.fcitx.Fcitx5.desktop']:
   dest=home/name;preserve(dest);dest.parent.mkdir(parents=True,exist_ok=True)
   src=root/'etc/skel'/name;shutil.copyfile(src,dest);dest.chmod(src.stat().st_mode&0o777);os.chown(dest,uid,account.pw_gid)
   parent=dest.parent
   while parent!=home:
    os.chown(parent,uid,account.pw_gid);parent=parent.parent
  for major in [3,4]:
   p=home/f'.config/gtk-{major}.0/settings.ini';preserve(p);cfg=configparser.ConfigParser(interpolation=None,strict=False);cfg.optionxform=str
   if p.exists():cfg.read(p)
   if not cfg.has_section('Settings'):cfg.add_section('Settings')
   cfg['Settings']['gtk-im-module']='fcitx';p.parent.mkdir(parents=True,exist_ok=True)
   with p.open('w') as f:cfg.write(f)
   os.chown(p,uid,account.pw_gid);os.chown(p.parent,uid,account.pw_gid)
  # Keep native Wayland toolkit input; provide XIM and Qt6 XWayland fallback.
  command(u+['systemctl','--user','unset-environment','QT_IM_MODULE','GTK_IM_MODULE','SDL_IM_MODULE'])
  command(u+['systemctl','--user','set-environment','XMODIFIERS=@im=fcitx','QT_IM_MODULES=wayland;fcitx;ibus'])
  command(u+['env','XMODIFIERS=@im=fcitx','QT_IM_MODULES=wayland;fcitx;ibus','dbus-update-activation-environment','--systemd','XMODIFIERS','QT_IM_MODULES'])
  command(['modprobe','uinput'])
  command(['systemctl','daemon-reload']);command(['systemctl','start','fcitx5-osk-key-helper.service'])
  # Desktop file is the rollback point; the current user's KWin layout is retained.
  preserve(home/'.config/kwinrc')
  for key,value in [('InputMethod','/usr/share/applications/fyi.fortime.Fcitx5Osk.KwinLauncher.desktop'),('VirtualKeyboardEnabled','true')]:
   command(u+['kwriteconfig6','--notify','--file','kwinrc','--group','Wayland','--key',key,value])
  command(u+['qdbus6','org.kde.KWin','/KWin','reconfigure'])
  time.sleep(2)
  result['helper']=command(['systemctl','is-active','fcitx5-osk-key-helper.service']).stdout.strip()
  result['fcitx_process']=command(['pgrep','-u',str(uid),'-a','-f','^/usr/bin/fcitx5'],check=False).stdout
  result['controller']=command(u+['busctl','--user','introspect','org.fcitx.Fcitx5','/controller','org.fcitx.Fcitx.Controller1'],check=False).stdout
  env_args=[f'{k}={v}' for k,v in session.items()]
  result['test_window']=command(u+['systemd-run','--user','--collect','--unit=f8-fcitx5-input-test','/usr/bin/env','-u','QT_IM_MODULE','-u','GTK_IM_MODULE',*env_args,'QT_QPA_PLATFORM=wayland','XMODIFIERS=@im=fcitx','QT_IM_MODULES=wayland;fcitx;ibus','/usr/bin/python3','-I','/usr/libexec/f8-pro/fcitx5-input-test.py']).returncode
 return result

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--package',required=True);p.add_argument('--user');p.add_argument('--install-packages',action='store_true');a=p.parse_args()
 print(json.dumps(install(a.root,a.package,a.user,a.install_packages),indent=2))
