"""Configure only the independent official-root copy for bounded GPU/Wayland trials."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

P=Path('/mnt/d/Netdisk/Other/F8-PRO/archlinux')
E=P/'analysis/armbian/official-gpu-baseline-20261029'
root=Path(json.loads((E/'prepared-official-root.json').read_text())['root_directory'])
assert root==Path('/var/tmp/f8-pro-armbian/f8-official-armbian-26.8.1/rootfs')
assert 'VERSION=26.8.1' in (root/'etc/armbian-release').read_text()
assert not (E/'graphics-root-integration.json').exists(),'Preserve completed integration'
release='6.1.115-vendor-rk35xx'
assert hashlib.sha256((root/f'boot/vmlinuz-{release}').read_bytes()).hexdigest()=='a67daf71caefef6b97a22ba708bbb302b239a4a9b4874cadd17a217ebd0c37b7'
assets=P/'armbian/official-graphics'
libexec=root/'usr/libexec/f8-pro';libexec.mkdir(parents=True,exist_ok=True);libexec.chmod(0o755)
installed=[]
for src,dest,mode in [(assets/'gpu-probe.py',libexec/'gpu-probe.py',0o644),
    (P/'tools/probe-gpu-context.py',libexec/'probe-gpu-context.py',0o644),
    *[(assets/(name+'.sh'),libexec/name,0o755) for name in ['graphics-run','wayland-run','wayland-client']]]:
    assert not dest.exists(),dest
    dest.write_bytes(src.read_bytes());dest.chmod(mode);installed.append(str(dest.relative_to(root)))
units=root/'etc/systemd/system';units.mkdir(parents=True,exist_ok=True)
for src in assets.glob('f8-*.service'):
    dest=units/src.name;assert not dest.exists();dest.write_bytes(src.read_bytes());dest.chmod(0o644)
src=assets/'f8-official-graphics.target'
dest=units/src.name;assert not dest.exists();dest.write_bytes(src.read_bytes());dest.chmod(0o644)
# Fresh trial account, locked password, no sudo. PAM/logind grant the DRM session.
assert not any(s.split(':')[0]=='f8gpu' or s.split(':')[2]=='1600' for s in (root/'etc/passwd').read_text().splitlines() if s)
with (root/'etc/passwd').open('a') as stream:stream.write('f8gpu:x:1600:1600:F8 GPU trial:/home/f8gpu:/bin/bash\n')
with (root/'etc/shadow').open('a') as stream:stream.write('f8gpu:!:1:0:99999:7:::\n')
groups=[]
for line in (root/'etc/group').read_text().splitlines():
    parts=line.split(':');assert parts[0]!='f8gpu' and parts[2]!='1600'
    if parts[0] in ['video','render']:
        parts[-1]=','.join([x for x in parts[-1].split(',') if x]+['f8gpu'])
    groups.append(':'.join(parts))
groups.append('f8gpu:x:1600:')
(root/'etc/group').write_text('\n'.join(groups)+'\n')
home=root/'home/f8gpu';home.mkdir(mode=0o750);os.chown(home,1600,1600)
masked=['armbian-firstrun.service','armbian-firstlogin.service','armbian-resize-filesystem.service',
        'armbian-zram-config.service','armbian-ramlog.service','armbian-hardware-optimize.service',
        'armbian-hardware-monitor.service','orangepi5-usb2-init.service','sddm.service',
        'ssh.service','ssh.socket','sshd.service','getty@tty1.service',
        'apt-daily.timer','apt-daily-upgrade.timer','dpkg-db-backup.timer','fstrim.timer',
        'systemd-pstore.service']
for name in masked:
    dest=units/name
    if dest.is_symlink() or dest.exists():dest.unlink()
    dest.symlink_to('/dev/null')
fstab=root/'etc/fstab';assert not fstab.is_symlink()
shutil.copy2(fstab,root/'etc/fstab.f8-official-source')
fstab.write_text('# F8 trial: root and /run mounted by initramfs, no physical filesystem writes.\n')
crypt=root/'etc/crypttab'
assert not crypt.exists() or not [s for s in crypt.read_text().splitlines() if s.strip() and not s.lstrip().startswith('#')]
for p in [root/'etc/machine-id',root/'var/lib/dbus/machine-id']:
    if p.is_symlink():continue
    if p.exists():p.write_bytes(b'')
hostkeys=list((root/'etc/ssh').glob('ssh_host_*_key*'))
for key in hostkeys:assert key.parent==root/'etc/ssh';key.unlink()
(root/'etc/hostname').write_text('f8-pro-armbian\n')
(root/'etc/f8-pro-official-trial').write_text('Armbian 26.8.1 official KDE base; F8 GPU/display trial; RAM overlay required\n')
deps={}
for name in ['squashfs','overlay','panel_simple','panthor']:
    r=subprocess.run(['modprobe','-d',str(root),'-S',release,'--show-depends',name],capture_output=True,text=True)
    assert r.returncode==0,(name,r.stderr)
    deps[name]=r.stdout.splitlines()
for name in ['graphics-run','wayland-run','wayland-client']:
    subprocess.run(['chroot',str(root),'/bin/sh','-n',f'/usr/libexec/f8-pro/{name}'],check=True,timeout=30)
probe=subprocess.run(['chroot',str(root),'/usr/bin/python3','-I','/usr/libexec/f8-pro/gpu-probe.py',
                      '--output','/tmp/f8-gpu-no-device.json'],capture_output=True,text=True,timeout=60)
assert probe.returncode==1,(probe.returncode,probe.stdout,probe.stderr)
fixture=json.loads((root/'tmp/f8-gpu-no-device.json').read_text())
assert fixture['hardware_accepted'] is False and 'Expected one Panthor render node' in fixture['error']
(root/'tmp/f8-gpu-no-device.json').unlink()
# Target report unit/timer are added when FIT/log export is packaged.
verify=subprocess.run(['systemd-analyze','--root='+str(root),'--man=no','verify',
                      'f8-official-graphics.service','f8-official-wayland.service'],capture_output=True,text=True)
(E/'graphics-units-verify.log').write_text(verify.stdout+verify.stderr)
assert verify.returncode==0,verify.stderr
mapfile=root/f'boot/System.map-{release}'
blacklist_found=mapfile.exists() and 'rockchip_cpufreq_driver_init' in mapfile.read_text()
report={'scope':'Independent official root copy configured offline; no target services or hardware run',
        'root_directory':str(root),'installed_assets':installed,'masked_trial_units':masked,
        'official_gpu_libraries_firmware_modules_preserved':True,'kernel_release':release,
        'locked_test_user':'f8gpu','test_uid':1600,'sudo_granted':False,
        'hostkeys_removed_count':len(hostkeys),'fstab_physical_entries_removed':True,
        'module_dependencies':deps,'qemu_arm64_shell_checks_passed':True,
        'qemu_arm64_no_gpu_rejected':fixture,'units_verify_passed':True,
        'cpufreq_blacklist_symbol_in_official_map':blacklist_found,
        'new_target_root_image_packed':False,'hardware_test_performed':False}
(E/'graphics-root-integration.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
