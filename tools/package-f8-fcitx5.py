"""Build a reviewable Fcitx5 runtime overlay from pinned source and ARM64 binaries."""
from pathlib import Path
import hashlib,json,shutil,subprocess,tarfile
P=Path(__file__).resolve().parents[1];A=P/'armbian/fcitx5';O=P/'outputs/armbian/f8-fcitx5-r1';R=O/'rootfs';R.mkdir(parents=True,exist_ok=True)
ref=(P/'local/fcitx5-osk-source/commit.txt').read_text().strip();S=P/'local/fcitx5-osk-source'/('fcitx5-osk-'+ref)
modes={}
def put(target,data,mode=0o644):
 modes[target]=mode
 p=R/target;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data if isinstance(data,bytes) else data.encode());p.chmod(mode)
def copy(src,dst,mode=0o644):put(dst,Path(src).read_bytes().removeprefix(b'\xef\xbb\xbf'),mode)
for name in ['fcitx5-osk','fcitx5-osk-kwin-launcher','fcitx5-osk-key-helper']:
 copy(O/name,'usr/bin/'+name,0o755)
 subprocess.run(['aarch64-linux-gnu-strip','--strip-unneeded',str(R/'usr/bin'/name)],check=True)
for name in ['fyi.fortime.Fcitx5Osk.desktop','fyi.fortime.Fcitx5Osk.KwinLauncher.desktop']:
 put('usr/share/applications/'+name,(S/'pkg/share/applications'/(name+'.in')).read_text().replace('@INSTALL_BIN_DIR@','/usr/bin'))
for name in ['fyi.fortime.Fcitx5Osk.service','fyi.fortime.Fcitx5Osk.KwinLauncher.service']:
 put('usr/share/dbus-1/services/'+name,(S/'pkg/share/dbus-1/services'/(name+'.in')).read_text().replace('@INSTALL_BIN_DIR@','/usr/bin'))
copy(S/'pkg/share/dbus-1/system.d/fyi.fortime.Fcitx5OskKeyHelper.conf','etc/dbus-1/system.d/fyi.fortime.Fcitx5OskKeyHelper.conf')
copy(S/'assets/icons/fcitx5-osk.svg','usr/share/icons/hicolor/scalable/apps/fyi.fortime.Fcitx5Osk.svg')
copy(S/'LICENSE','usr/share/licenses/fcitx5-osk/LICENSE')
copy(P/'downloads/nerd-fonts-symbols-3.4.0/SymbolsNerdFont-Regular.ttf','usr/share/fonts/truetype/f8-pro/SymbolsNerdFont-Regular.ttf')
copy(P/'downloads/nerd-fonts-symbols-3.4.0/LICENSE','usr/share/licenses/f8-nerd-fonts-symbols/LICENSE')
for f in (S/'pkg/share/fcitx5-osk').rglob('*.toml'):
 if f.name not in ['otp.toml','pw.toml']:copy(f,'usr/share/fcitx5-osk/'+f.relative_to(S/'pkg/share/fcitx5-osk').as_posix())
copy(S/'pkg/share/fcitx5-osk/themes/breeze-light.toml','etc/xdg/fcitx5-osk/themes/breeze-light.toml')
for src,dst,mode in [
 ('key-helper.service','etc/systemd/system/fcitx5-osk-key-helper.service',0o644),
 ('key-helper.toml','etc/fcitx5-osk-key-helper/config.toml',0o644),
 ('session-env.sh','etc/skel/.config/plasma-workspace/env/f8-fcitx5.sh',0o755),
 ('environment.conf','etc/skel/.config/environment.d/60-f8-fcitx5.conf',0o644),
 ('profile','etc/skel/.config/fcitx5/profile',0o644),('config','etc/skel/.config/fcitx5/config',0o644),
 ('osk-config.toml','etc/skel/.config/fcitx5-osk/config.toml',0o644),
 ('kwinrc','etc/skel/.config/kwinrc',0o644),
 ('switch-keyboard.py','usr/libexec/f8-pro/switch-keyboard.py',0o755),
 ('input-test.py','usr/libexec/f8-pro/fcitx5-input-test.py',0o644),
 ('rollback.desktop','usr/share/applications/f8-plasma-keyboard.desktop',0o644),
 ('enable.desktop','usr/share/applications/f8-chinese-keyboard.desktop',0o644)]:copy(A/src,dst,mode)
# KWin owns the input-method socket. Avoid a competing generic desktop autostart.
put('etc/skel/.config/autostart/org.fcitx.Fcitx5.desktop','[Desktop Entry]\nType=Application\nName=Fcitx5\nHidden=true\n')
put('etc/skel/.gtkrc-2.0','gtk-im-module="fcitx"\n')
for major in [3,4]:put(f'etc/skel/.config/gtk-{major}.0/settings.ini','[Settings]\ngtk-im-module=fcitx\n')
put('etc/modules-load.d/f8-fcitx5-osk.conf','uinput\n')
links={f'etc/systemd/system/{t}.wants/fcitx5-osk-key-helper.service':'../fcitx5-osk-key-helper.service' for t in ['multi-user.target','f8-desktop.target']}
files={str(f.relative_to(R)).replace('\\','/'):dict(sha256=hashlib.sha256(f.read_bytes()).hexdigest(),mode=modes[str(f.relative_to(R)).replace('\\','/')],bytes=f.stat().st_size) for f in R.rglob('*') if f.is_file()}
manifest=dict(version='r1',symbol_font_version='3.4.0',symbol_font_source='https://github.com/ryanoasis/nerd-fonts',source_commit=ref,source='https://github.com/fortime/fcitx5-osk',haptic_patch_sha256=hashlib.sha256((A/'patch-osk-haptic.py').read_bytes()).hexdigest(),http_actions_enabled=False,kwin_binary_plugin_enabled=False,packages=[x for x in (A/'packages.txt').read_text().splitlines() if x and not x.startswith('#')],files=files,links=links)
(O/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
with tarfile.open(O/'f8-fcitx5-r1.tar.gz','w:gz') as t:
 t.add(O/'manifest.json',arcname='manifest.json',filter=lambda i: (setattr(i,'mode',0o644) or i));
 def permissions(info):
  info.mode=0o755 if info.isdir() else modes.get(info.name.removeprefix('rootfs/'),0o644)
  return info
 t.add(R,arcname='rootfs',filter=permissions)
print(json.dumps(dict(files=len(files),tar_bytes=(O/'f8-fcitx5-r1.tar.gz').stat().st_size)))
