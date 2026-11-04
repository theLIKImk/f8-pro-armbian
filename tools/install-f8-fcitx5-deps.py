import os,json,subprocess
from pathlib import Path
assert os.geteuid()==0 and os.environ.get('SUDO_USER')=='likimk'
packages=['fcitx5','fcitx5-chinese-addons','fcitx5-config-qt','fcitx5-frontend-qt5','fcitx5-frontend-qt6','fcitx5-frontend-gtk3','fcitx5-frontend-gtk4']
a=['systemd-run','--unit=f8-fcitx5-deps','--collect','--setenv=DEBIAN_FRONTEND=noninteractive','/usr/bin/apt-get','-y','--no-install-recommends','install',*packages]
r=subprocess.run(a,capture_output=True,text=True,timeout=10)
print(json.dumps({'exit':r.returncode,'stdout':r.stdout,'stderr':r.stderr,'uinput':Path('/dev/uinput').exists(),'os_release':Path('/etc/os-release').read_text()}))
