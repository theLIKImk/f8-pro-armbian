import json,subprocess,os
from pathlib import Path
env=dict(os.environ,DEBIAN_FRONTEND='noninteractive')
r=subprocess.run(['apt-get','-y','--no-install-recommends','install','fcitx5-module-cloudpinyin'],capture_output=True,text=True,timeout=55,env=env)
o={'apt_exit':r.returncode,'apt_tail':r.stdout[-2000:],'apt_stderr':r.stderr[-600:],'files':{}}
if r.returncode==0:
 for p in [Path('/usr/share/fcitx5/addon/cloudpinyin.conf'),Path('/usr/share/fcitx5/configdesc/cloudpinyin.desc')]:
  if p.exists():o['files'][str(p)]=p.read_text()
 o['package_files']=subprocess.check_output(['dpkg','-L','fcitx5-module-cloudpinyin'],text=True)
print(json.dumps(o))
