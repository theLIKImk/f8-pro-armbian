import json,subprocess,os
from pathlib import Path
def run(a,timeout=12):
 r=subprocess.run(a,capture_output=True,text=True,timeout=timeout);return {'exit':r.returncode,'out':r.stdout[:8000],'err':r.stderr[:500]}
o={'cloud_packages':run(['apt-cache','policy','fcitx5-module-cloudpinyin','fcitx5-chinese-addons','fcitx5-chinese-addons-bin']),'cloud_files':run(['sh','-c','dpkg -L fcitx5-module-cloudpinyin 2>/dev/null | head -40']),'storage':run(['df','-h','/']),'blocks':run(['lsblk','-o','NAME,SIZE,TYPE,FSTYPE,MOUNTPOINTS,PARTLABEL,UUID']),'fcitx_config':{}}
for p in [Path('/home/likimk/.config/fcitx5/conf/pinyin.conf'),Path('/home/likimk/.config/fcitx5/conf/cloudpinyin.conf'),Path('/usr/share/fcitx5/addon/cloudpinyin.conf')]:
 if p.exists():o['fcitx_config'][str(p)]=p.read_text()
print(json.dumps(o))
