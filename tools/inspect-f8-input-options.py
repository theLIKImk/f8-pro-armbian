import json,subprocess,pwd
from pathlib import Path
u=['runuser','-u','likimk','--','env','XDG_RUNTIME_DIR=/run/user/1602','DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1602/bus']
def run(a):
 r=subprocess.run(a,capture_output=True,text=True,timeout=15);return dict(exit=r.returncode,stdout=r.stdout,stderr=r.stderr)
o={'packages':run(['apt-cache','policy','fcitx5-osk','fcitx5-virtualkeyboard','qt6-virtualkeyboard-plugin','plasma-keyboard']),'layouts':run(['dpkg','-L','qt6-virtualkeyboard-plugin']),'keyboard_config':Path('/home/likimk/.config/plasmakeyboardrc').read_text(),'desktop':Path('/usr/share/applications/org.kde.plasma.keyboard.desktop').read_text(),'tools':run(['sh','-c','command -v cargo; command -v cmake; command -v fcitx5-remote; command -v qdbus6; command -v kdialog']),'disk':run(['df','-h','/']),'fcitx_service':run(u+['busctl','--user','list','--no-pager'])}
print(json.dumps(o))
