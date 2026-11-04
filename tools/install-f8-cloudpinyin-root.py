"""Install cloud-pinyin package and non-personal defaults into an explicit root."""
from pathlib import Path
import argparse,os,subprocess,hashlib,json,re
P=Path(__file__).resolve().parents[1]
def install(root,packages=False):
 R=Path(root).resolve();assert os.geteuid()==0 and (R/'etc').is_dir();prefix=[] if R==Path('/') else ['chroot',str(R)]
 if packages:subprocess.run(prefix+['apt-get','-y','--no-install-recommends','install','fcitx5-module-cloudpinyin'],check=True,env=dict(os.environ,DEBIAN_FRONTEND='noninteractive'),capture_output=True,timeout=300)
 v=subprocess.check_output(prefix+['dpkg-query','-W','-f=${Status} ${Version}','fcitx5-module-cloudpinyin'],text=True);assert v.startswith('install ok installed')
 result={}
 for n in ['pinyin.conf','cloudpinyin.conf']:
  data=(P/'armbian/fcitx5-cloud'/n).read_text(encoding='utf-8-sig')
  p=R/'etc/skel/.config/fcitx5/conf'/n;p.parent.mkdir(parents=True,exist_ok=True)
  old=p.read_text() if p.exists() else ''
  for row in data.splitlines():
   k,sep,value=row.partition('=')
   if not sep:continue
   if re.search(r'^'+re.escape(k)+r'=.*$',old,flags=re.M):old=re.sub(r'^'+re.escape(k)+r'=.*$',row,old,flags=re.M)
   else:old=old.rstrip()+'\n'+row+'\n'
  p.write_text(old.lstrip());p.chmod(0o644);result[str(p.relative_to(R))]=hashlib.sha256(p.read_bytes()).hexdigest()
 return {'package':v,'files':result,'backend':'Baidu','personal_input_history_copied':False}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--install-packages',action='store_true');a=p.parse_args();print(json.dumps(install(a.root,a.install_packages)))
