import json,pwd,subprocess,os
from pathlib import Path
uid=pwd.getpwnam('likimk').pw_uid
u=['runuser','-u','likimk','--','env',f'XDG_RUNTIME_DIR=/run/user/{uid}',f'DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/{uid}/bus']
def run(a):
 r=subprocess.run(a,capture_output=True,text=True,timeout=12);return dict(exit=r.returncode,stdout=r.stdout,stderr=r.stderr)
patterns=['fcitx5*','fcitx*','maliit*','im-config','libqt5*fcitx*','libfcitx*']
o={'packages':run(['dpkg-query','-W','-f=${binary:Package} ${Version} ${db:Status-Abbrev}\\n',*patterns]),'candidates':run(['apt-cache','policy','fcitx5','fcitx5-chinese-addons','fcitx5-pinyin','fcitx5-frontend-qt5','fcitx5-frontend-qt6','fcitx5-frontend-gtk3','fcitx5-frontend-gtk4']),'env':run(u+['systemctl','--user','show-environment']),'process':run(['pgrep','-af','fcitx|maliit']),'configs':{}}
for name in ['/home/likimk/.config/kwinrc','/home/likimk/.config/fcitx5/config','/home/likimk/.config/fcitx5/profile','/home/likimk/.xinputrc','/etc/environment','/etc/default/im-config']:
 p=Path(name)
 if p.is_file():o['configs'][name]=p.read_text(errors='replace')
print(json.dumps(o))
