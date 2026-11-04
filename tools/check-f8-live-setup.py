"""Exercise RAM-only setup with synthetic credentials in an isolated overlay."""
import json
import os
from pathlib import Path
import subprocess
P=Path('/mnt/d/Netdisk/Other/F8-PRO/archlinux')
base=Path('/var/tmp/f8-pro-armbian/live-setup-fixture-v4');base.mkdir(exist_ok=True)
lower=Path('/var/tmp/f8-pro-armbian/f8-official-armbian-26.8.1/rootfs')
for name in ['upper','work','root','run','container','firmware']:(base/name).mkdir(exist_ok=True)
root=base/'root';container=base/'container'
profile=container/'etc/NetworkManager/system-connections';profile.mkdir(parents=True,exist_ok=True)
(profile/'fixture.nmconnection').write_text('[connection]\nid=fixture\n')
authorized=container/'home/alarm/.ssh';authorized.mkdir(parents=True,exist_ok=True)
keys=container/'etc/ssh';keys.mkdir(parents=True,exist_ok=True)
key=keys/'ssh_host_ed25519_key'
if not key.exists():subprocess.run(['ssh-keygen','-q','-t','ed25519','-N','','-f',str(key)],check=True)
(authorized/'authorized_keys').write_bytes(key.with_suffix('.pub').read_bytes())
firmware=P/'analysis/armbian/wireless/verified-assets.json'
source=Path(json.loads(firmware.read_text())['staging_directory'])/'usr/lib/firmware/ap6275p'
subprocess.run(['cp','-a',str(source)+'/.',str(base/'firmware')],check=True)
script=(P/'armbian/official-graphics/live-setup.sh').read_text()
script=script.replace('r=/\n','r='+str(root)+'\n').replace('c=/run/f8/container','c='+str(container))
path=base/'setup.sh';path.write_text(script)
fwscript=(P/'armbian/official-graphics/live-firmware-setup.sh').read_text()
fwscript=fwscript.replace('r=/mnt/root','r='+str(root)).replace('/f8-live-firmware/*',str(base/'firmware')+'/*')
fwpath=base/'firmware-setup.sh';fwpath.write_text(fwscript)
busybox=Path('/var/tmp/f8-pro-armbian/official-live-g6-r2/busybox')
applets=base/'applets';applets.mkdir(exist_ok=True)
for name in ['cp','rm','mkdir','chmod','mount','umount','chroot']:
    wrapper=applets/name
    wrapper.write_text('#!/bin/sh\nexec /usr/bin/qemu-aarch64-static '+str(busybox)+' '+name+' "$@"\n')
    wrapper.chmod(0o755)
environment=dict(os.environ,PATH=str(applets)+':/usr/sbin:/usr/bin:/sbin:/bin')
subprocess.run(['mount','-t','overlay','overlay','-o',f'lowerdir={lower},upperdir={base}/upper,workdir={base}/work',str(root)],check=True)
try:
    # Seed the same collision seen in the real initramfs. The fix must replace it.
    fw=root/'usr/lib/firmware/ap6275p';fw.mkdir(parents=True,exist_ok=True)
    existing=fw/'nvram_ap6275p.txt'
    if existing.exists() or existing.is_symlink():existing.unlink()
    existing.symlink_to('nvram_AP6275P.txt')
    fwresult=subprocess.run(['qemu-aarch64-static',str(busybox),'sh',str(fwpath)],env=environment,capture_output=True,text=True,timeout=25)
    assert fwresult.returncode==0,fwresult.stderr
    assert existing.is_symlink() and existing.readlink()==Path('nvram_AP6275P.txt')
    for entry in json.loads(firmware.read_text())['files']:
        if entry['path'].startswith('usr/lib/firmware/ap6275p/'):
            assert (fw/Path(entry['path']).name).read_bytes()==(source/Path(entry['path']).name).read_bytes()
    # Native target provisioning now runs only after systemd provides these mounts.
    for directory,src in [('run',base/'run'),('dev',Path('/dev')),('proc',Path('/proc'))]:
        (root/directory).mkdir(exist_ok=True)
        subprocess.run(['mount','--bind',str(src),str(root/directory)],check=True)
    result=subprocess.run(['qemu-aarch64-static',str(busybox),'sh',str(path)],env=environment,capture_output=True,text=True,timeout=60)
    if result.returncode:raise RuntimeError(result.stderr[-2000:])
    try:
        check=subprocess.run(['chroot',str(root),'/usr/sbin/sshd','-T','-f','/run/f8/sshd_config'],capture_output=True,text=True)
        assert check.returncode==0,check.stderr
        for line in ['passwordauthentication no','kbdinteractiveauthentication no','permitrootlogin no','allowusers f8test']:
            assert line in check.stdout,line
    finally:
        subprocess.run(['umount',str(root/'proc')],check=True)
        subprocess.run(['umount',str(root/'dev')],check=True)
        subprocess.run(['umount',str(root/'run')],check=True)
    assert (root/'home/f8test/.ssh/authorized_keys').read_bytes()==(authorized/'authorized_keys').read_bytes()
    assert (root/'home/f8test/.ssh/authorized_keys').stat().st_mode&0o777==0o600
    assert not (lower/'home/f8test').exists()
    report={'synthetic_credential_setup_passed':True,'sshd_configuration_verified':True,
      'password_login_disabled':True,'official_root_unchanged':True,'network_or_authentication_tested':False,
      'actual_initramfs_busybox_applets_used':True,'existing_firmware_symlink_replacement_passed':True,
      'provisioning_has_proc_dev_run':True,'firmware_bytes_and_aliases_verified':True}
    out=P/'analysis/armbian/live-g6';out.mkdir(exist_ok=True)
    (out/'setup-fixture-systemd-r4.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report))
finally:subprocess.run(['umount',str(root)],check=True)
