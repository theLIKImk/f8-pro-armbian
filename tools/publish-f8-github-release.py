"""Publish an existing verified archive. Token is accepted on stdin only.

This tool is not part of the image build and never touches the tablet.
"""
from pathlib import Path
import hashlib,json,os,sys,time,requests,subprocess,base64

P=Path(__file__).resolve().parents[1]
O=P/'outputs/armbian/f8-armbian-20261103-r2'
W=P/'local/github-publish-20261104'
W.mkdir(parents=True,exist_ok=True)
S=W/'release-assets';S.mkdir(exist_ok=True)
TOKEN=sys.stdin.read().strip();assert TOKEN
API='https://api.github.com/repos/theLIKImk/f8-pro-armbian'
TAG='v2026.11.03-r2'
session=requests.Session()
session.headers.update({'Authorization':'Bearer '+TOKEN,'Accept':'application/vnd.github+json','User-Agent':'F8-release-publisher','X-GitHub-Api-Version':'2022-11-28'})

def progress(phase,**kw):
 (W/'upload-progress.json').write_text(json.dumps({'phase':phase,'time':time.time(),**kw},indent=2),encoding='utf-8')
 print(json.dumps({'phase':phase,**kw}),flush=True)
def api(method,url,**kw):
 r=session.request(method,url,timeout=90,**kw)
 if not r.ok:raise RuntimeError(f'GitHub API {r.status_code}: '+r.text[:800])
 return r.json() if r.content else None
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

try:
 archive=O/'F8_ARMBIAN_20261103_R2_BOOT_ROOTFS.zip'
 expected=json.loads((O/'bundle.json').read_text())
 assert archive.stat().st_size==expected['bytes']
 size=1900*1024**2;whole=hashlib.sha256();parts=[]
 progress('splitting_and_verifying_archive')
 with archive.open('rb') as f:
  i=1
  while f.tell()<archive.stat().st_size:
   dest=S/(archive.name+f'.{i:03d}');h=hashlib.sha256();remaining=min(size,archive.stat().st_size-f.tell())
   with dest.open('wb') as d:
    while remaining:
     data=f.read(min(8*1024**2,remaining));assert data
     d.write(data);whole.update(data);h.update(data);remaining-=len(data)
   parts.append({'name':dest.name,'bytes':dest.stat().st_size,'sha256':h.hexdigest()});i+=1
 assert whole.hexdigest()==expected['sha256'],'Original archive hash mismatch'
 manifest={'original':expected,'parts':parts,'concatenation_order':[p['name'] for p in parts]}
 (S/'split-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
 (S/'SHA256SUMS-parts.txt').write_text(''.join(x['sha256']+'  '+x['name']+'\n' for x in parts),encoding='ascii')
 for name in ['manifest.json','privacy-audit.json','checks-summary.json','ZIP-SHA256.txt','SHA256SUMS','README-刷入说明.txt']:
  (S/name).write_bytes((O/name).read_bytes())
 (S/'merge-release.py').write_text('''from pathlib import Path
import hashlib,json,os
p=Path(__file__).resolve().parent
m=json.loads((p/'split-manifest.json').read_text(encoding='utf-8'))
dest=p/m['original']['archive'];tmp=dest.with_suffix(dest.suffix+'.joining')
if dest.exists():raise SystemExit('Output already exists; move it aside before merging.')
whole=hashlib.sha256()
try:
 with tmp.open('xb') as out:
  for part in m['parts']:
   h=hashlib.sha256();src=p/part['name']
   if src.stat().st_size!=part['bytes']:raise ValueError('Size mismatch: '+src.name)
   with src.open('rb') as f:
    while data:=f.read(8*1024**2):out.write(data);h.update(data);whole.update(data)
   if h.hexdigest()!=part['sha256']:raise ValueError('Checksum mismatch: '+src.name)
   print('Verified:',src.name)
 if whole.hexdigest()!=m['original']['sha256']:raise ValueError('Merged archive checksum mismatch')
 os.rename(tmp,dest)
 print('Verified archive:',dest)
except BaseException:
 if tmp.exists():tmp.unlink()
 raise
''',encoding='utf-8')
 progress('parts_ready',parts=parts)
 while not (W/'source-pushed.json').exists():time.sleep(5)
 commit=json.loads((W/'source-pushed.json').read_text())['commit']
 body='''F8-PRO RK3588S · Armbian / KDE Plasma Wayland 测试镜像。

完整包约4.70 GiB，拆为三个连续分卷。下载全部 `.zip.001`、`.zip.002`、`.zip.003`、`split-manifest.json` 和 `merge-release.py` 到同一目录，运行 `python merge-release.py`，校验并合并后解压 ZIP。不要单独解压分卷。分卷、合并 ZIP 及内部镜像均提供 SHA-256。

包含 Fcitx5 中文实体/屏幕键盘、百度云拼音、当前适配的音频/相机/传感器中继等。Wi-Fi 密码/连接、SSH 主机及用户密钥、旧账户与个人目录已清除；SSH 默认关闭，启用时生成新密钥。云拼音会发送拼音查询，可在设置关闭。

仅适用于本项目已验证的 F8 分区布局：BOOT 0x00008000、ROOTFS 0x00078000；不刷 Loader/uboot/分区表。刷写会覆盖系统与账户，请先备份。BOOT 64MiB，ROOTFS 解压后16GiB，首次启动预期自动扩容。

文件系统检查、87项关键文件回读、隐私检查、ZIP CRC及向导6页离屏预览通过。本份完整包尚未进行实际新刷/冷启动验收。电池/充电采样、多指近距触摸、相机高级控制等限制仍存在。详细说明见仓库 README 和附件刷入说明。
'''
 existing=session.get(API+'/releases/tags/'+TAG,timeout=60)
 if existing.status_code==404:
  release=api('POST',API+'/releases',json={'tag_name':TAG,'target_commitish':commit,'name':'F8 Armbian 2026-11-03 R2 · 测试版','body':body,'draft':True,'prerelease':True})
 else:
  existing.raise_for_status();release=existing.json();assert release['draft'],'Do not overwrite a published release'
 assets=api('GET',API+f"/releases/{release['id']}/assets?per_page=100")
 uploaded=[]
 class Reader:
  def __init__(self,f,name):self.f=f;self.name=name;self.last=0
  def __getattr__(self,n):return getattr(self.f,n)
  def read(self,n=-1):
   data=self.f.read(n)
   if time.time()-self.last>5:
    self.last=time.time();progress('uploading',name=self.name,sent=self.f.tell(),total=os.fstat(self.f.fileno()).st_size)
   return data
 for path in sorted(S.iterdir()):
  if not path.is_file():continue
  digest=sha(path)
  old=next((a for a in assets if a['name']==path.name),None)
  if old:
   assert old['size']==path.stat().st_size and old.get('digest')=='sha256:'+digest,'Existing asset mismatch'
   asset=old
  else:
   progress('uploading',name=path.name,sent=0,total=path.stat().st_size)
   with path.open('rb') as f:
    response=session.post(release['upload_url'].split('{')[0],params={'name':path.name},headers={'Content-Type':'application/octet-stream'},data=Reader(f,path.name),timeout=(60,3600))
   if not response.ok:raise RuntimeError(f'Asset upload {response.status_code}: '+response.text[:800])
   asset=response.json()
   assert asset['size']==path.stat().st_size and asset.get('digest')=='sha256:'+digest,'Server digest mismatch'
  uploaded.append({'name':path.name,'bytes':asset['size'],'sha256':digest,'url':asset['browser_download_url']})
  (W/'uploaded-assets.json').write_text(json.dumps(uploaded,indent=2),encoding='utf-8')
  progress('asset_verified',name=path.name,bytes=asset['size'])
 # Publish only after every attachment has passed GitHub's size and SHA-256 check.
 release=api('PATCH',API+f"/releases/{release['id']}",json={'draft':False,'prerelease':True,'body':body})
 result={'complete':True,'release_url':release['html_url'],'tag':TAG,'commit':commit,'assets':uploaded}
 (W/'published.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
 progress('complete',url=release['html_url'],assets=len(uploaded))
except BaseException as e:
 progress('failed',error=str(e).replace(TOKEN,'[REDACTED]'))
 raise SystemExit(1)
finally:
 session.close();TOKEN=None
