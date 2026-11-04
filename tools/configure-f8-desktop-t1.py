"""Integrate SDDM/Plasma Wayland into the independent official-root copy."""
import hashlib
import importlib.util
import gzip
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'tools'))
from inspect_images import fdt
root=Path('/var/tmp/f8-pro-armbian/desktop-t1/rootfs')
out=P/'outputs/armbian/official-f8-desktop-t1'
assert (out/'keyboard-installation.json').exists()
assert not (out/'desktop-integration.json').exists(),'Preserve completed desktop integration'
r6=P/'outputs/armbian/official-f8-live-g6-r6';meta=json.loads((r6/'preflight.json').read_text())
assert meta['r6_cold_boot_verified'] and meta['sampling_persistence_verified']
blob=(r6/meta['candidate_file']).read_bytes();assert hashlib.sha256(blob).hexdigest()==meta['candidate_sha256']
fit=fdt(blob);prop=fit['/images/ramdisk'];a=int.from_bytes(prop['data-position'],'big');n=int.from_bytes(prop['data-size'],'big')
spec=importlib.util.spec_from_file_location('cpio',P/'tools/build-usb-bootlog.py')
helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
records={name:body for name,values,body in helper.cpio_read(gzip.decompress(blob[a:a+n]))}
libexec=root/'usr/libexec/f8-pro';libexec.mkdir(exist_ok=True)
units=root/'etc/systemd/system'
for name,body in records.items():
    if not name.startswith('f8-g3-assets/'):continue
    short=Path(name).name;dest=units/short if short.endswith(('.service','.target','.timer')) else libexec/short
    if dest.is_symlink():dest.unlink()
    dest.write_bytes(body);dest.chmod(0o644 if short.endswith(('.service','.target','.timer','.py','.ko')) else 0o755)
fw=root/'usr/lib/firmware/ap6275p';fw.mkdir(exist_ok=True)
recordlist=helper.cpio_read(gzip.decompress(blob[a:a+n]))
for name,values,body in recordlist:
    if not name.startswith('f8-live-firmware/'):continue
    dest=fw/Path(name).name
    if dest.exists() or dest.is_symlink():dest.unlink()
    if values[1]&0o170000==0o120000:dest.symlink_to(body.decode())
    else:dest.write_bytes(body)
desktop=P/'armbian/desktop-t1'
for source in desktop.iterdir():
    dest=libexec/source.name;dest.write_bytes(source.read_bytes());dest.chmod(0o644 if source.suffix=='.py' else 0o755)
target='''[Unit]
Description=F8 official Armbian full Plasma Wayland desktop test
Requires=basic.target
After=basic.target
Wants=f8-live-prepare.service f8-live-network.service f8-live-ssh.service f8-live-power.service f8-live-status.service f8-desktop-hardware.service sddm.service f8-official-report.timer systemd-timesyncd.service
AllowIsolate=yes
'''
(units/'f8-desktop.target').write_text(target)
prepare=(units/'f8-live-prepare.service').read_text().replace('/usr/libexec/f8-pro/live-setup.sh','/usr/libexec/f8-pro/desktop-prepare.sh')
(units/'f8-live-prepare.service').write_text(prepare)
(units/'f8-desktop-hardware.service').write_text('''[Unit]
Description=F8 verified GPU panel and touch initialization
Wants=f8-live-status.service systemd-logind.service
After=basic.target f8-live-status.service systemd-logind.service
Before=sddm.service
[Service]
Type=oneshot
ExecStart=/bin/sh /usr/libexec/f8-pro/desktop-hardware.sh
RemainAfterExit=yes
TimeoutStartSec=80
''')
mask=units/'sddm.service'
assert mask.is_symlink() and os.readlink(mask)=='/dev/null';mask.unlink()
(root/'etc/X11/default-display-manager').write_text('/usr/bin/sddm\n')
drop=units/'sddm.service.d';drop.mkdir(exist_ok=True)
(drop/'90-f8-desktop.conf').write_text('''[Unit]
Requires=f8-live-prepare.service f8-desktop-hardware.service
Wants=systemd-user-sessions.service systemd-logind.service
After=f8-live-prepare.service f8-desktop-hardware.service systemd-user-sessions.service systemd-logind.service
[Service]
RestartSec=5
''')
configs=root/'etc/sddm.conf.d';configs.mkdir(exist_ok=True)
backup=root/'etc/sddm.f8-source';backup.mkdir(exist_ok=True)
for old in [root/'etc/sddm.conf',*configs.glob('*.conf')]:
    if old.is_file() and not old.is_symlink():shutil.copyfile(old,backup/old.name)
    if old.exists() or old.is_symlink():old.unlink()
assert (root/'usr/bin/plasma-keyboard').is_file()
assert (root/'usr/share/applications/org.kde.plasma.keyboard.desktop').is_file()
(configs/'90-f8-wayland.conf').write_text('''[General]
DisplayServer=wayland
GreeterEnvironment=QT_WAYLAND_SHELL_INTEGRATION=layer-shell
InputMethod=
[Theme]
Current=breeze
[Wayland]
CompositorCommand=/usr/bin/kwin_wayland --drm --no-global-shortcuts --no-lockscreen --inputmethod /usr/bin/plasma-keyboard --locale1
[Autologin]
User=f8test
Session=plasma.desktop
Relogin=false
''')
assert (root/'usr/share/sddm/themes/breeze').is_dir()
skel=root/'etc/skel';config=skel/'.config';config.mkdir(exist_ok=True)
(config/'kwinrc').write_text('[Wayland]\nInputMethod=/usr/share/applications/org.kde.plasma.keyboard.desktop\n')
(config/'kscreenlockerrc').write_text('[Daemon]\nAutolock=false\nLockOnResume=false\n')
home=skel/'Desktop';home.mkdir(exist_ok=True)
(config/'user-dirs.dirs').write_text('XDG_DESKTOP_DIR="$HOME/Desktop"\n')
launchers={
 'F8-Test-Status.desktop':'''[Desktop Entry]
Type=Application
Name=F8 Test Status
Name[zh_CN]=测试状态
Icon=utilities-system-monitor
Exec=konsole --hold -e sudo -n python3 /usr/libexec/f8-pro/desktop-status.py
Terminal=false
''',
 'F8-Keyboard.desktop':'''[Desktop Entry]
Type=Application
Name=On-screen Keyboard Settings
Name[zh_CN]=屏幕键盘设置
Icon=input-keyboard-virtual
Exec=systemsettings kcm_virtualkeyboard
Terminal=false
''',
 'F8-Network.desktop':'''[Desktop Entry]
Type=Application
Name=Network Settings
Name[zh_CN]=网络设置
Icon=network-wireless
Exec=systemsettings kcm_networkmanagement
Terminal=false
'''}
for name,text in launchers.items():
    path=home/name;path.write_text(text);path.chmod(0o755)
autostart=root/'etc/xdg/autostart/f8-desktop-session-record.desktop'
autostart.write_text('''[Desktop Entry]
Type=Application
Name=F8 desktop session evidence
Exec=/bin/sh /usr/libexec/f8-pro/desktop-session-record.sh
OnlyShowIn=KDE;
NoDisplay=true
''')
for name in ['sleep.target','suspend.target','hibernate.target','hybrid-sleep.target','suspend-then-hibernate.target']:
    path=units/name
    if path.exists() or path.is_symlink():path.unlink()
    path.symlink_to('/dev/null')
(units/'f8-official-report.timer').write_text('''[Unit]
Description=Export F8 desktop boot evidence
[Timer]
OnActiveSec=150s
AccuracySec=1s
Unit=f8-official-report.service
''')
# Extend the proven logger with desktop evidence; keep USB export read-only.
logger=records['f8-evaluation-report'].decode().replace('ARMBIAN-G6','ARMBIAN-DESKTOP-T1').replace('F8PROAG6','F8PROADT1').replace('f8_official_armbian_g6','f8_official_desktop_t1')
logger=logger.replace('f8-official-graphics.target','f8-desktop.target')
anchor='    cat /etc/armbian-release >"$disk/ARMBIAN.TXT" 2>&1\n';assert anchor in logger
logger=logger.replace(anchor,anchor+'''    timeout 10 journalctl -b -u sddm.service -u f8-desktop-hardware.service --no-pager -n 300 >"$disk/DESKTOP.TXT" 2>&1
    timeout 10 journalctl -b _UID=1601 --no-pager -n 250 >"$disk/USERDESK.TXT" 2>&1
    [ ! -f /run/user/1601/f8-desktop/session.json ] || cp /run/user/1601/f8-desktop/session.json "$disk/SESSION.JSON"
    [ ! -f /run/user/1601/f8-desktop/kwin-info.txt ] || cp /run/user/1601/f8-desktop/kwin-info.txt "$disk/KWINFO.TXT"
    systemctl --no-pager show sddm.service f8-desktop-hardware.service -p ActiveState -p SubState -p Result -p ExecMainStatus >"$disk/DMSTATE.TXT" 2>&1
''')
(libexec/'graphics-report').write_text(logger);(libexec/'graphics-report').chmod(0o755)
(root/'etc/f8-pro-desktop-t1').write_text('Official Armbian 26.8.1 desktop T1; F8 r6 hardware; RAM overlay test\n')
(root/'etc/fstab').write_text('# Desktop T1: all writes are RAM overlay; original container ro,noload.\n')
assert not list((root/'etc/ssh').glob('ssh_host_*_key'))
assert not (root/'home/f8test').exists()
report={'root':str(root),'base':'Official Armbian 26.8.1 with exact verified r6 Image/DT/modules',
 'sddm_wayland_only':True,'desktop_session':'plasma.desktop','test_autologin_user':'f8test',
 'keyboard':'plasma-keyboard 6.6.4 + Qt6 virtual keyboard plugin','desktop_settings_persistent':False,
 'private_credentials_in_image':False,'suspend_disabled_for_unvalidated_hardware':True,
 'automatic_old_popup_disabled':True,'hardware_test_performed':False}
(out/'desktop-integration.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
