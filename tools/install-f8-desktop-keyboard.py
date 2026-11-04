"""Install three pinned keyboard packages only into the independent desktop root."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
P=Path(__file__).resolve().parents[1]
work=Path('/var/tmp/f8-pro-armbian/desktop-t1');root=work/'rootfs'
out=P/'outputs/armbian/official-f8-desktop-t1'
assert (work/'copy-complete.json').exists(),'Wait for independent copy'
marker=out/'keyboard-installation.json';assert not marker.exists(),'Preserve completed installation'
packages=['plasma-keyboard=6.6.4-0ubuntu1','qt6-virtualkeyboard-plugin=6.10.2+dfsg-1']
critical=['sddm','plasma-workspace','kwin-wayland','libegl-mesa0','libgbm1','libgl1-mesa-dri']
def versions():
    return subprocess.check_output(['chroot',str(root),'dpkg-query','-W',*critical],text=True)
before=versions();kernel=root/'boot/vmlinuz-6.1.115-vendor-rk35xx';kernelhash=hashlib.sha256(kernel.read_bytes()).hexdigest()
simulation=subprocess.run(['chroot',str(root),'apt-get','-s','--no-upgrade','--no-install-recommends','install',*packages],capture_output=True,text=True,timeout=120)
(out/'keyboard-apt-simulation.log').write_text(simulation.stdout+simulation.stderr)
assert simulation.returncode==0,simulation.stderr[-1000:]
assert not re.search(r'^Remv |^Inst \S+ \[',simulation.stdout,re.M),'Refuse package removal or upgrade'
resolv=root/'etc/resolv.conf';saved_resolv=('link',os.readlink(resolv)) if resolv.is_symlink() else ('file',resolv.read_bytes())
policy=root/'usr/sbin/policy-rc.d';saved_policy=policy.read_bytes() if policy.exists() else None
mounts=[]
try:
    for part in ['dev','proc','sys','run']:
        (root/part).mkdir(exist_ok=True)
        subprocess.run(['mount','--bind','/'+part,str(root/part)],check=True);mounts.append(part)
    resolv.unlink();resolv.write_bytes(Path('/etc/resolv.conf').read_bytes())
    policy.write_text('#!/bin/sh\nexit 101\n');policy.chmod(0o755)
    env=dict(os.environ,DEBIAN_FRONTEND='noninteractive')
    with (out/'keyboard-apt-install.log').open('w') as log:
        result=subprocess.run(['chroot',str(root),'apt-get','-y','--no-upgrade','--no-install-recommends',
           '-o','DPkg::Options::=--force-confold','install',*packages],env=env,stdout=log,stderr=subprocess.STDOUT,timeout=600)
    assert result.returncode==0,(out/'keyboard-apt-install.log').read_text()[-2000:]
finally:
    if resolv.exists() or resolv.is_symlink():resolv.unlink()
    if saved_resolv[0]=='link':resolv.symlink_to(saved_resolv[1])
    else:resolv.write_bytes(saved_resolv[1])
    if saved_policy is None:policy.unlink(missing_ok=True)
    else:policy.write_bytes(saved_policy)
    for part in reversed(mounts):subprocess.run(['umount',str(root/part)],check=True)
after=versions();assert before==after and hashlib.sha256(kernel.read_bytes()).hexdigest()==kernelhash
report={'root':str(root),'critical_packages_unchanged':True,'critical_versions':after,
 'installed':subprocess.check_output(['chroot',str(root),'dpkg-query','-W','plasma-keyboard','qt6-virtualkeyboard-plugin','qml6-module-org-kde-layershell'],text=True),
 'no_target_device_writes':True}
marker.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
