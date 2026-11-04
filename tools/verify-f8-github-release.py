"""Verify the public release independently; credentials arrive on stdin only."""
from pathlib import Path
import json,sys,urllib.request,hashlib,time
P=Path(__file__).resolve().parents[1];W=P/'local/github-publish-20261104';S=W/'release-assets'
token=sys.stdin.read().strip();API='https://api.github.com/repos/theLIKImk/f8-pro-armbian'
def request(path,authenticated=False,method='GET'):
 headers={'User-Agent':'F8-release-verifier','Accept':'application/vnd.github+json'}
 if authenticated:headers['Authorization']='Bearer '+token
 with urllib.request.urlopen(urllib.request.Request(API+path,headers=headers,method=method),timeout=60) as response:
  return json.load(response) if method!='DELETE' else None
release=request('/releases/tags/v2026.11.03-r2')
assert not release['draft'] and release['prerelease']
assets=release['assets'];checks=[]
parts={x['name']:x for x in json.loads((S/'split-manifest.json').read_text(encoding='utf-8'))['parts']}
for path in sorted(S.iterdir()):
 if not path.is_file():continue
 if path.name in parts:
  assert path.stat().st_size==parts[path.name]['bytes'];digest=parts[path.name]['sha256']
 else:
  with path.open('rb') as f:digest=hashlib.file_digest(f,'sha256').hexdigest()
 matches=[a for a in assets if a.get('digest')=='sha256:'+digest and a['size']==path.stat().st_size]
 assert len(matches)==1,path.name
 asset=matches[0];assert asset['state']=='uploaded'
 checks.append({'local_name':path.name,'name':asset['name'],'bytes':asset['size'],'sha256':digest,'url':asset['browser_download_url']})
 # Public download must work for a small actual attachment, not only the API.
 if path.name=='split-manifest.json':
  with urllib.request.urlopen(urllib.request.Request(asset['browser_download_url'],headers={'User-Agent':'F8-release-verifier'}),timeout=60) as r:data=r.read()
  assert hashlib.sha256(data).hexdigest()==digest
assert len(checks)==len(assets)
tag=request('/git/ref/tags/v2026.11.03-r2');previous=json.loads((W/'published.json').read_text());expected=previous.get('commit',previous.get('tag_commit'))
assert tag['object']['type']=='commit' and tag['object']['sha']==expected
# Remove only the abandoned draft created by this task before the upload switch.
cleanup=[]
for draft in request('/releases?per_page=100',True):
 if draft['id']==433358280:
  assert draft['draft'] and draft['tag_name']=='v2026.11.03-r2'
  assert len(draft['assets'])<=1 and all(a['name']=='checks-summary.json' for a in draft['assets'])
  request('/releases/'+str(draft['id']),True,'DELETE');cleanup.append(draft['id'])
result={'complete':True,'public_release_verified':True,'release_url':release['html_url'],'tag_commit':expected,'assets':checks,'public_manifest_download_verified':True,'abandoned_own_drafts_removed':cleanup,'time':time.time()}
(W/'public-verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
(W/'published.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps({'complete':True,'url':release['html_url'],'assets':len(checks),'tag_commit':expected,'public_manifest_download_verified':True,'cleaned_drafts':cleanup}))
