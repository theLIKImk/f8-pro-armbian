"""Pin public Rockchip U-Boot reference sources for analysis; never execute them."""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import urllib.request

P=Path(__file__).resolve().parents[1]
out=P/'analysis/armbian/loader-source-reference'
out.mkdir(parents=True,exist_ok=True)
def get(url):
    req=urllib.request.Request(url,headers={'User-Agent':'F8-PRO-offline-port-audit'})
    with urllib.request.urlopen(req,timeout=45) as response:
        return response.read()
pin=out/'pin.json'
if pin.exists():
    metadata=json.loads(pin.read_text())
else:
    commit=json.loads(get('https://api.github.com/repos/rockchip-linux/u-boot/commits/next-dev'))
    metadata={'repository':'rockchip-linux/u-boot','reference_branch':'next-dev','commit':commit['sha'],
              'scope':'Public reference only; not proven to match archived tablet U-Boot'}
    pin.write_text(json.dumps(metadata,indent=2)+'\n')
treefile=out/'tree.json'
if treefile.exists():
    tree=json.loads(treefile.read_text())
else:
    tree=json.loads(get('https://api.github.com/repos/rockchip-linux/u-boot/git/trees/'+metadata['commit']+'?recursive=1'))
    assert not tree.get('truncated')
    treefile.write_text(json.dumps(tree)+'\n')
paths=[item['path'] for item in tree['tree'] if item['type']=='blob' and
       ((('fit' in item['path'].lower() or 'boot_rkimg' in item['path']) and item['path'].endswith(('.c','.h')) and
         item['path'].startswith(('common/','arch/arm/mach-rockchip/','include/','cmd/'))) or
        item['path'] in ['common/bootm.c','common/image-fdt.c','arch/arm/lib/bootm.c','arch/arm/mach-rockchip/board.c'])]
def fetch(path):
    target=out/path
    target.parent.mkdir(parents=True,exist_ok=True)
    url='https://raw.githubusercontent.com/rockchip-linux/u-boot/'+metadata['commit']+'/'+path
    data=target.read_bytes() if target.exists() else get(url)
    if not target.exists():target.write_bytes(data)
    return {'path':path,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'url':url}
with ThreadPoolExecutor(max_workers=4) as pool:
    files=list(pool.map(fetch,paths))
(out/'manifest.json').write_text(json.dumps({**metadata,'files':files},indent=2)+'\n')
print(json.dumps({'commit':metadata['commit'],'files':len(files),'bytes':sum(i['bytes'] for i in files)}))
