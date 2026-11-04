"""Validate desktop service graph and synthetic first-login provisioning in overlay."""
import hashlib
import argparse
import json
import os
from pathlib import Path
import subprocess
P=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--native',action='store_true');args=parser.parse_args()
root=Path('/var/tmp/f8-pro-armbian/desktop-t1/rootfs')
out=P/'outputs/armbian/official-f8-desktop-t1'
assert (out/'desktop-integration.json').exists()
resultname='desktop-native-validation.json' if args.native else 'desktop-validation.json'
assert not (out/resultname).exists(),'Preserve completed validation'
critical=json.loads((out/'keyboard-installation.json').read_text())['critical_versions']
pins=[]
for line in critical.splitlines():
    name,version=line.split('\t');pins.append(f'Package: {name}\nPin: version {version}\nPin-Priority: 1001\n')
pinpath=root/'etc/apt/preferences.d/99-f8-desktop-baseline';pinpath.parent.mkdir(exist_ok=True)
pinpath.write_text('\n'.join(pins))
unitnames=['f8-desktop.target','f8-desktop-hardware.service','f8-live-prepare.service',
 'f8-live-network.service','f8-live-ssh.service','f8-live-power.service','f8-live-status.service','sddm.service','f8-official-report.timer','f8-official-report.service']
verify=subprocess.run(['systemd-analyze','--root='+str(root),'--man=no','verify',*unitnames],capture_output=True,text=True)
(out/'desktop-units-verify.log').write_text(verify.stdout+verify.stderr)
assert verify.returncode==0,verify.stderr
work=Path('/var/tmp/f8-pro-armbian/desktop-t1-validation-native' if args.native else '/var/tmp/f8-pro-armbian/desktop-t1-validation')
for part in ['upper','work','root','run']:(work/part).mkdir(parents=True,exist_ok=True)
trial=work/'root';container=work/'run/f8/container'
network=container/'etc/NetworkManager/system-connections';network.mkdir(parents=True,exist_ok=True)
(network/'fixture.nmconnection').write_text('[connection]\nid=fixture\n')
keys=container/'etc/ssh';keys.mkdir(parents=True,exist_ok=True)
key=keys/'ssh_host_ed25519_key'
if not key.exists():subprocess.run(['ssh-keygen','-q','-t','ed25519','-N','','-f',str(key)],check=True)
auth=container/'home/alarm/.ssh';auth.mkdir(parents=True,exist_ok=True)
(auth/'authorized_keys').write_bytes(key.with_suffix('.pub').read_bytes())
subprocess.run(['mount','-t','overlay','overlay','-o',f'lowerdir={root},upperdir={work}/upper,workdir={work}/work',str(trial)],check=True)
mounts=[]
try:
    for name,source in [('dev',Path('/dev')),('proc',Path('/proc')),('sys',Path('/sys')),('run',work/'run')]:
        subprocess.run(['mount','--bind',str(source),str(trial/name)],check=True);mounts.append(name)
    # Native /bin/sh uses the full virtual filesystems, as on the tablet.
    result=subprocess.run(['chroot',str(trial),'/bin/sh','/usr/libexec/f8-pro/desktop-prepare.sh'],capture_output=True,text=True,timeout=60)
    (out/'synthetic-desktop-provisioning.log').write_text(result.stdout+result.stderr)
    assert result.returncode==0,result.stderr[-2000:]
    assert 'InputMethod=/usr/share/applications/org.kde.plasma.keyboard.desktop' in (trial/'home/f8test/.config/kwinrc').read_text()
    assert (trial/'home/f8test/.config/kwinrc').stat().st_uid==1601
    expectedauth=(root/'usr/share/f8-pro/test-authorized-keys') if args.native else (auth/'authorized_keys')
    assert (trial/'home/f8test/.ssh/authorized_keys').read_bytes()==expectedauth.read_bytes()
    if args.native:
        assert (trial/'etc/ssh/ssh_host_ed25519_key').is_file()
        assert (trial/'etc/ssh/ssh_host_ed25519_key.pub').is_file()
    groups=subprocess.check_output(['chroot',str(trial),'/usr/bin/id','-nG','f8test'],text=True).split()
    assert {'video','render','nopasswdlogin'}<=set(groups)
    cli={}
    for binary in ['kwin_wayland','plasma-keyboard']:
        r=subprocess.run(['chroot',str(trial),'/usr/bin/env','QT_QPA_PLATFORM=offscreen',
                          '/usr/bin/'+binary,'--help'],capture_output=True,text=True,timeout=45)
        (out/(binary+'-help.txt')).write_text(r.stdout+r.stderr)
        cli[binary]=r.returncode
        assert r.returncode==0,(binary,r.stderr[-1200:])
    assert '--inputmethod' in (out/'kwin_wayland-help.txt').read_text()
    # startplasma-wayland does not implement --help; it attempts a real session.
    assert (trial/'usr/bin/startplasma-wayland').is_file()
    for binary in ['sddm','plasma-keyboard','kwin_wayland']:
        r=subprocess.run(['chroot',str(trial),'/usr/bin/ldd','/usr/bin/'+binary],capture_output=True,text=True,timeout=30)
        (out/(binary+'-libraries.txt')).write_text(r.stdout+r.stderr)
        assert r.returncode==0 and 'not found' not in r.stdout,(binary,r.stderr)
finally:
    for name in reversed(mounts):subprocess.run(['umount',str(trial/name)],check=True)
    subprocess.run(['umount',str(trial)],check=True)
assert not (root/'home/f8test').exists()
assert not list((root/'etc/ssh').glob('ssh_host_*_key'))
assert not (root/'etc/machine-id').read_bytes()
for name in ['run','dev','proc','sys']:assert subprocess.run(['mountpoint','-q',str(root/name)]).returncode!=0
report={'unit_graph_verified':True,'synthetic_desktop_user_and_ssh_verified':True,
 'video_render_groups_verified':True,'keyboard_default_copied_and_owned':True,
 'arm64_help_exit_codes':cli,'sddm_keyboard_kwin_shared_libraries_resolved':True,
 'private_fixture_material_not_in_root':True,'critical_versions_pinned':True,
 'kernel_sha256':hashlib.sha256((root/'boot/vmlinuz-6.1.115-vendor-rk35xx').read_bytes()).hexdigest(),
    'real_desktop_hardware_test_performed':False,'native_first_boot_mode':args.native}
(out/resultname).write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
