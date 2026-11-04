"""Sanitize ONLY the isolated snapshot, then install first-run and defaults."""
from pathlib import Path
import hashlib,json,os,re,shutil,subprocess
P=Path(__file__).resolve().parents[1];B=Path(os.environ.get('F8_RELEASE_DIR','/var/tmp/f8-pro-armbian/release-r1'));R=B/'rootfs'
assert B.parent.resolve()==Path('/var/tmp/f8-pro-armbian') and re.fullmatch(r'release-[a-z0-9-]+',B.name)
assert R.resolve()==B.resolve()/'rootfs'
assert (B/'snapshot-complete.json').exists()
assert not (B/'configured.json').exists()
for row in Path('/proc/self/mountinfo').read_text().splitlines():
 mount=Path(row.split()[4]);assert mount!=R and not mount.is_relative_to(R),'Refuse mounted snapshot'
def put(name,text,mode=0o644):
 p=R/name.lstrip('/');p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text);p.chmod(mode)
def remove(name):
 p=R/name.lstrip('/');assert p.is_relative_to(R) and p!=R
 if p.is_symlink() or p.is_file():p.unlink()
 elif p.is_dir():shutil.rmtree(p)
def copy(source,dest,mode=0o644):
 p=R/dest.lstrip('/');p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,p);p.chmod(mode)
# Fresh public SSH defaults: never copy client/server identities from the live tablet.
put('etc/ssh/ssh_config','Include /etc/ssh/ssh_config.d/*.conf\nHost *\n    SendEnv LANG LC_*\n    HashKnownHosts yes\n')
put('etc/ssh/sshd_config','Include /etc/ssh/sshd_config.d/*.conf\nPermitRootLogin no\nPasswordAuthentication yes\nKbdInteractiveAuthentication no\nUsePAM yes\nX11Forwarding no\nPrintMotd no\nAcceptEnv LANG LC_*\nSubsystem sftp /usr/lib/openssh/sftp-server\n')
(R/'etc/ssh/ssh_config.d').mkdir(parents=True,exist_ok=True)
put('etc/systemd/system/ssh.service.d/10-f8-new-hostkeys.conf','[Service]\nExecStartPre=\nExecStartPre=/usr/bin/ssh-keygen -A\nExecStartPre=/usr/sbin/sshd -t\n')
# Rebuild account databases without test users or any password hashes.
old={'f8gpu','f8test','f8setup'}|{line.split(':')[0] for line in (R/'etc/passwd').read_text().splitlines() if 1000<=int(line.split(':')[2])<60000}
passwd=[x for x in (R/'etc/passwd').read_text().splitlines() if x.split(':')[0] not in old]
assert not any(int(x.split(':')[2])==1601 for x in passwd)
passwd.append('f8setup:x:1601:1601:F8 First Run:/home/f8setup:/bin/bash')
put('etc/passwd','\n'.join(passwd)+'\n')
put('etc/shadow',''.join(f'{x.split(":")[0]}:*:20000:0:99999:7:::\n' for x in passwd),0o640)
groups=[];gids=set()
for row in (R/'etc/group').read_text().splitlines():
 parts=row.split(':')
 if parts[0] in old:continue
 members=[n for n in parts[3].split(',') if n and n not in old]
 if parts[0] in {'video','render','audio','netdev','nopasswdlogin'}:members.append('f8setup')
 parts[3]=','.join(members);groups.append(':'.join(parts));gids.add(int(parts[2]))
assert 1601 not in gids;groups.append('f8setup:x:1601:')
if not any(x.startswith('nopasswdlogin:') for x in groups):groups.append('nopasswdlogin:x:1599:f8setup')
put('etc/group','\n'.join(groups)+'\n');put('etc/gshadow',''.join(x.split(':')[0]+':!::'+x.split(':')[3]+'\n' for x in groups),0o640)
shadow_gid=int(next(x.split(':')[2] for x in groups if x.startswith('shadow:')))
os.chown(R/'etc/shadow',0,shadow_gid);os.chown(R/'etc/gshadow',0,shadow_gid)
for name in ['passwd-','shadow-','group-','gshadow-','subuid','subuid-','subgid','subgid-']:
 remove('etc/'+name)
put('etc/subuid','');put('etc/subgid','')
for name in ['etc/security/opasswd','etc/security/opasswd.old','etc/ppp/chap-secrets','etc/ppp/pap-secrets']:
 if (R/name).is_file():put(name,'',0o600)
for pat in ['etc/ssh/ssh_host_*','etc/*~','etc/.*.swp']:
 for f in R.glob(pat):remove(str(f.relative_to(R)))
for name in ['home','root','var/lib/NetworkManager','var/lib/bluetooth','var/lib/sddm','var/lib/f8-pro','var/lib/dbus/machine-id','var/lib/systemd/random-seed','var/lib/systemd/credential.secret','var/lib/libuuid/clock.txt','etc/ssh/moduli.old','usr/share/f8-pro/test-authorized-keys','etc/sudoers.d/f8-live-test','etc/sudoers.d/90-armbian','etc/f8-pro-desktop-t1','var/cache','var/log','var/log.hdd','var/tmp','tmp']:
 remove(name)
for name in ['dev','proc','sys','run','tmp','mnt','media','home','root','var/tmp','var/log','var/cache','var/lib/f8-pro','var/lib/NetworkManager','var/lib/bluetooth','var/lib/sddm','etc/NetworkManager/system-connections']:
 p=R/name;p.mkdir(parents=True,exist_ok=True)
 if name in {'tmp','var/tmp'}:p.chmod(0o1777)
 if name=='root':p.chmod(0o700)
# Basic offline chroot devices; no host bind mounts or live-root writes.
import stat
for device,major,minor in [('null',1,3),('zero',1,5),('random',1,8),('urandom',1,9),('tty',5,0)]:
 p=R/'dev'/device
 if not p.exists():os.mknod(p,stat.S_IFCHR|0o666,os.makedev(major,minor))
put('etc/machine-id','');(R/'var/lib/dbus').mkdir(exist_ok=True);(R/'var/lib/dbus/machine-id').symlink_to('/etc/machine-id')
put('etc/hostname','f8-pad\n');put('etc/hosts','127.0.0.1 localhost\n127.0.1.1 f8-pad\n::1 localhost\n')
remove('etc/netplan')
put('etc/netplan/00-default-use-network-manager.yaml','network:\n  version: 2\n  renderer: NetworkManager\n',0o600)
put('etc/f8-pro-release-r1','F8 Armbian KDE Wayland R1 first-run test\n')
copy(P/'armbian/first-run/native-prepare.sh','usr/libexec/f8-pro/native-prepare.sh',0o755)
put('usr/libexec/f8-pro/desktop-prepare.sh','#!/bin/sh\nset -eu\nexec /bin/sh /usr/libexec/f8-pro/native-prepare.sh\n',0o755)
for name in ['first-run.py','first-run-apply.py']:copy(P/'armbian/first-run'/name,'usr/local/lib/f8-pro/'+name,0o755)
copy(P/'armbian/first-run/setup-cleanup.py','usr/local/lib/f8-pro/setup-cleanup.py',0o755)
for name in ['f8-setup-cleanup.service','f8-setup-cleanup.timer']:
 copy(P/'armbian/first-run'/name,'etc/systemd/system/'+name)
cleanup_link=R/'etc/systemd/system/f8-desktop.target.wants/f8-setup-cleanup.timer'
cleanup_link.parent.mkdir(exist_ok=True)
if cleanup_link.exists() or cleanup_link.is_symlink():cleanup_link.unlink()
cleanup_link.symlink_to('../f8-setup-cleanup.timer')
copy(P/'armbian/first-run/root-grow-r1a.py','usr/local/lib/f8-pro/root-grow-r1a.py',0o755)
copy(P/'armbian/first-run/f8-root-grow-r1a.service','etc/systemd/system/f8-root-grow-r1a.service')
grow_link=R/'etc/systemd/system/f8-desktop.target.wants/f8-root-grow-r1a.service'
if grow_link.exists() or grow_link.is_symlink():grow_link.unlink()
grow_link.symlink_to('../f8-root-grow-r1a.service')
copy(P/'armbian/first-run/f8-first-run.desktop','etc/xdg/autostart/f8-first-run.desktop')
copy(P/'armbian/first-run/f8-guide.desktop','usr/share/applications/f8-guide.desktop')
put('etc/sudoers.d/f8-first-run','f8setup ALL=(root) NOPASSWD: /usr/local/lib/f8-pro/first-run-apply.py ""\n',0o440)
put('etc/sddm.conf.d/99-f8-first-run.conf','[Autologin]\nUser=f8setup\nSession=plasma.desktop\nRelogin=false\n')
base_sddm=R/'etc/sddm.conf.d/90-f8-wayland.conf'
base_sddm.write_text(base_sddm.read_text().split('[Autologin]')[0])
# Make defaults apply to every new user; no saved compass calibration or history.
skel=R/'etc/skel';remove('etc/skel/Desktop/F8-Test-Status.desktop')
for name in ['.config/kwinrc','.config/plasmakeyboardrc','.config/kscreenlockerrc','.config/f8-cover.json','.config/systemd/user/f8-cover-screen.service']:
 copy(B/'user-defaults'/name,'etc/skel/'+name)
put('etc/skel/.config/plasmakeyboardrc','[General]\nenabledLocales=en_US\nkeyboardNavigationEnabled=true\nsoundEnabled=true\nvibrationEnabled=true\nvibrationMs=30\n')
put('etc/skel/.config/kwinrc','[Wayland]\nInputMethod=/usr/share/applications/org.kde.plasma.keyboard.desktop\nVirtualKeyboardEnabled=true\n')
# Chrony must be enabled for the systemd.unit=f8-desktop.target boot path.
subprocess.run(['/usr/bin/python3',str(P/'tools/install-f8-time-sync-root.py'),'--root',str(R),'--install-packages'],check=True)
# QtLocation QML alone is insufficient: explicitly include the OSM provider.
subprocess.run(['/usr/bin/python3',str(P/'tools/install-f8-kde-timezone-root.py'),'--root',str(R),'--install-packages'],check=True)
# Enable Chinese lunar calendar for each new user without hardcoding widget IDs.
subprocess.run(['/usr/bin/python3',str(P/'tools/install-f8-calendar-root.py'),'--root',str(R),'--install-packages'],check=True)
# Sensor fusion viewers and identified optical sensor are rootfs assets, not a new BOOT.
subprocess.run(['/usr/bin/python3',str(P/'tools/install-f8-sensors-f2-root.py'),'--root',str(R)],check=True)
# Standard measured IIO/session D-Bus relay and optional relative-light brightness.
subprocess.run(['/usr/bin/python3',str(P/'tools/install-f8-sensor-relay-root.py'),'--root',str(R)],check=True)
# Fcitx5 is installed before cloning skel, so setup and future accounts match.
subprocess.run(['/usr/bin/python3',str(P/'tools/install-f8-fcitx5-root.py'),'--root',str(R),'--package',str(P/'outputs/armbian/f8-fcitx5-r1'),'--install-packages'],check=True)
subprocess.run(['/usr/bin/python3',str(P/'tools/install-f8-cloudpinyin-root.py'),'--root',str(R),'--install-packages'],check=True)
link=skel/'.config/systemd/user/graphical-session.target.wants/f8-cover-screen.service';link.parent.mkdir(parents=True,exist_ok=True)
if link.exists() or link.is_symlink():link.unlink()
link.symlink_to('../f8-cover-screen.service')
desktop=skel/'Desktop';desktop.mkdir(exist_ok=True)
for f in (R/'usr/share/applications').glob('f8-*.desktop'):
 copy(f,'etc/skel/Desktop/'+f.name,0o755)
# Remove old status launcher from all skeleton locations.
remove('etc/skel/.ssh')
for personal in ['compass-calibration.json','optical-calibration.json','sensor-relay.json']:remove('etc/skel/.config/f8-pro/'+personal)
home=R/'home/f8setup';shutil.copytree(skel,home)
for path in [home,*home.rglob('*')]:os.chown(path,1601,1601,follow_symlinks=False)
# No diagnostic USB gadget export, test SSH, or user evidence collection on normal boot.
target=R/'etc/systemd/system/f8-desktop.target'
text=target.read_text().replace(' f8-live-ssh.service','').replace(' f8-official-report.timer','')
target.write_text(text)
for f in (R/'etc/systemd/system').glob('*.wants/*'):
 if f.name in {'ssh.service','ssh.socket','f8-live-ssh.service','f8-official-report.timer'}:remove(str(f.relative_to(R)))
for name in ['ssh.service','ssh.socket','sshd.service']:
 f=R/'etc/systemd/system'/name
 if f.is_symlink() and os.readlink(f)=='/dev/null':f.unlink()
sshd=R/'etc/ssh/sshd_config'
sshd.write_text(re.sub(r'^PermitRootLogin\s+\S+', 'PermitRootLogin no',sshd.read_text(),flags=re.M))
put('etc/ssh/sshd_config.d/00-f8-local-account.conf','PermitRootLogin no\nPasswordAuthentication yes\nKbdInteractiveAuthentication no\n')
# Remain disabled by default, but a user's normal `systemctl enable ssh`
# must also work with the tablet's custom default target.
put('etc/systemd/system/ssh.service.d/50-f8-target.conf','[Install]\nWantedBy=f8-desktop.target\n')
# polkit 127's socket helper requires newer kernel pidfd features. On this
# vendor 6.1 kernel use its standard authenticated setuid fallback instead.
helper=R/'usr/lib/polkit-1/polkit-agent-helper-1'
assert helper.is_file() and not helper.is_symlink()
os.chown(helper,0,0);helper.chmod(0o4755)
override=R/'var/lib/dpkg/statoverride'
rows=override.read_text().splitlines() if override.exists() else []
helper_name='/usr/lib/polkit-1/polkit-agent-helper-1'
matching=[row for row in rows if row.split() and row.split()[-1]==helper_name]
assert len(matching)<=1
assert not matching or matching[0].split()[:3] in [['root','root','755'],['root','root','4755']]
put('var/lib/dpkg/statoverride','\n'.join([row for row in rows if row not in matching]+['root root 4755 '+helper_name])+'\n')
for unit in (R/'usr/lib/systemd/system').glob('polkit-agent-helper*'):
 if unit.suffix in {'.service','.socket'}:
  remove('etc/systemd/system/'+unit.name)
  (R/'etc/systemd/system'/unit.name).symlink_to('/dev/null')
remove('etc/xdg/autostart/f8-desktop-session-record.desktop')
status=R/'usr/libexec/f8-pro/live-status.py'
if status.exists():status.write_text(status.read_text().replace('USER f8test / KEY AUTH','FIRST-RUN / LOCAL LOGIN'))
# Replace the f8test-only network exception with the local setup user's access.
rule=R/'etc/polkit-1/rules.d/49-f8-test-network.rules'
if rule.exists():rule.write_text(rule.read_text().replace('subject.user === "f8test"','subject.user === "f8setup"'))
copy(P/'armbian/input/70-f8-cover-haptic.rules','etc/udev/rules.d/70-f8-cover-haptic.rules')
copy(P/'armbian/audio/ucm2/HiFi.conf','usr/share/alsa/ucm2/F8-PRO/HiFi.conf')
for name in ['performance_state.py','performance-panel.py','performance-apply.py','performance-startup.py']:
 copy(P/'armbian/power'/name,'usr/local/lib/f8-pro/'+name,0o644 if name=='performance_state.py' else 0o755)
copy(P/'armbian/power/performance-limits.json','etc/f8-pro/performance-limits.json')
copy(P/'armbian/power/org.f8pro.performance.policy','usr/share/polkit-1/actions/org.f8pro.performance.policy')
copy(P/'armbian/power/f8-performance.desktop','usr/share/applications/f8-performance.desktop')
copy(P/'armbian/power/f8-performance.desktop','etc/skel/Desktop/f8-performance.desktop',0o755)
copy(P/'armbian/power/f8-performance.desktop','home/f8setup/Desktop/f8-performance.desktop',0o755)
os.chown(R/'home/f8setup/Desktop/f8-performance.desktop',1601,1601)
module=P/'outputs/armbian/f8-cpu-p3/f8-cpufreq-p3.ko'
assert hashlib.sha256(module.read_bytes()).hexdigest()==json.loads((P/'armbian/power/performance-limits.json').read_text())['cpu_module_sha256']
copy(module,'usr/local/lib/f8-pro/experimental/f8-cpufreq-p3.ko')
for name in ['f8-performance-gpu-start.service','f8-performance-cpu-start.service']:
 copy(P/'armbian/power'/name,'etc/systemd/system/'+name)
 link=R/'etc/systemd/system/f8-desktop.target.wants'/name
 if link.exists() or link.is_symlink():link.unlink()
 link.symlink_to('../'+name)
# Native KDE monitoring fixes: keep distribution updates outside Qt's plugin
# search directory and audit the exact runtime versions used for this build.
kde_assets=P/'outputs/armbian/f8-kde-monitor-k1'
kde_manifest=json.loads((kde_assets/'manifest.json').read_text())
installed={}
for stanza in (R/'var/lib/dpkg/status').read_text().split('\n\n'):
 fields=dict(line.split(': ',1) for line in stanza.splitlines() if ': ' in line and not line.startswith(' '))
 if 'Package' in fields and 'Version' in fields:installed[fields['Package']]=fields['Version']
for package,version in kde_manifest['versions'].items():assert installed.get(package)==version,('KDE monitor runtime version changed; rebuild plugins',package)
kde_critical=[]
for name,item in kde_manifest['plugins'].items():
 assert name in {'ksystemstats_plugin_gpu.so','ksystemstats_plugin_disk.so'}
 assert hashlib.sha256((kde_assets/name).read_bytes()).hexdigest()==item['sha256']
 destination='/usr/lib/aarch64-linux-gnu/qt6/plugins/ksystemstats/'+name
 diverted='/usr/lib/f8-pro/ksystemstats-distribution/'+name
 (R/diverted.lstrip('/')).parent.mkdir(parents=True,exist_ok=True)
 actual=subprocess.check_output(['dpkg-divert','--root='+str(R),'--truename',destination],text=True).strip()
 assert actual in {destination,diverted},'Unknown existing KDE plugin diversion'
 if actual==destination:subprocess.run(['dpkg-divert','--root='+str(R),'--local','--add','--rename','--divert',diverted,destination],check=True,capture_output=True)
 copy(kde_assets/name,destination)
 kde_critical.extend([destination.lstrip('/'),diverted.lstrip('/')])
# Clean obsolete first-login gate: graphical wizard replaces the console password prompt.
for name in ['root/.not_logged_in_yet','etc/profile.d/armbian-check-first-login.sh']:
 remove(name)
# Preserve the C4 init root UUID exactly; hardware boot itself remains unchanged.
put('etc/fstab','UUID=69056675-4a48-4006-a3f3-5132c00cc6f2 / ext4 defaults,noatime 0 1\n')
critical=['usr/local/lib/f8-pro/sensor-monitor.py','usr/local/lib/f8-pro/sensor_examples.py','usr/local/lib/f8-pro/motion_examples_math.py','usr/local/lib/f8-pro/camera-preview.py','usr/local/lib/f8-pro/libf8-camera-relay-view.so','usr/local/bin/f8-chromium-camera','usr/local/bin/f8-kamoso','usr/share/alsa/ucm2/F8-PRO/HiFi.conf','usr/share/wireplumber/wireplumber.conf.d/50-f8-ucm.conf','var/lib/alsa/asound.state','etc/systemd/system/f8-usb-otg.service','etc/systemd/system/f8-bluetooth.service','etc/systemd/system/f8-motion.service','etc/modules-load.d/f8-cover-haptic.conf','lib/modules/6.1.115-vendor-rk35xx/extra/f8-pro/f8-cover-haptic.ko','usr/local/lib/f8-pro/first-run-apply.py']
hashes={}
critical += ['usr/local/lib/f8-pro/setup-cleanup.py','etc/systemd/system/f8-setup-cleanup.service','etc/systemd/system/f8-setup-cleanup.timer','usr/local/lib/f8-pro/root-grow-r1a.py','etc/systemd/system/f8-root-grow-r1a.service']
critical += kde_critical
for name in critical:
 p=R/name;assert p.is_file(),name;hashes['/'+name]=hashlib.sha256(p.read_bytes()).hexdigest()
assert hashes['/lib/modules/6.1.115-vendor-rk35xx/extra/f8-pro/f8-cover-haptic.ko']=='a33e43d75e77ca997527608b2f97ab1971ae04bf7127be3d123e7172a05fcc4c'
report={'root':str(R),'critical_files':hashes,'first_user':'f8setup','setup_sudo_scope':'single helper, no arguments','wifi_and_host_private_keys_removed':True,'personal_homes_not_copied':True,'root_uuid':'69056675-4a48-4006-a3f3-5132c00cc6f2','source_boot':'current tablet partition, read-only snapshot','device_modified':False,'cold_boot_tested':False}
(B/'configured.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
