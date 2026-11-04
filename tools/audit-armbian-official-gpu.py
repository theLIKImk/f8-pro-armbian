"""Pin official Armbian GPU integration and image metadata; never deploy."""
import concurrent.futures
import hashlib
import json
from pathlib import Path
import urllib.request

P = Path(__file__).resolve().parents[1]
OUT = P/'analysis/armbian/official-gpu-baseline-20261029'
OUT.mkdir(parents=True, exist_ok=True)
PIN = '98692adee6442f6f221200cf8e6642f9c6a7b740'

def get(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'F8-PRO-official-baseline-audit'})
    with urllib.request.urlopen(req, timeout=45) as r:
        return r.read()

def save(url, path):
    data = get(url)
    dest = OUT/path
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        assert dest.read_bytes() == data, f'Preserve existing evidence: {dest}'
    else:
        dest.write_bytes(data)
    return {'url': url, 'path': path, 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}

tree_path = OUT/'build-tree.json'
if not tree_path.exists():
    tree_path.write_bytes(get(f'https://api.github.com/repos/armbian/build/git/trees/{PIN}?recursive=1'))
tree = json.loads(tree_path.read_bytes())
assert not tree.get('truncated'), 'Need complete official tree listing'
paths = [x['path'] for x in tree['tree'] if x['type']=='blob' and (
    'panthor' in x['path'].lower() or
    x['path'] in ['config/boards/orangepi5.conf', 'config/boards/rock-5b.conf',
                 'config/sources/families/include/rockchip_vendor_common.inc',
                 'config/kernel/linux-rk35xx-vendor.config'] or
    (x['path'].startswith('config/desktop/trixie/') and 'packages' in x['path']))]

def fetch(path):
    try:
        return save(f'https://raw.githubusercontent.com/armbian/build/{PIN}/{path}', 'build/'+path)
    except Exception as error:
        return {'path': path, 'error': str(error)}

with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
    records = list(pool.map(fetch, paths))
for repo in ['os']:
    try:
        path=f'{repo}-latest-release.json'
        record=save(f'https://api.github.com/repos/armbian/{repo}/releases/latest', path)
        records.append(record)
        obj=json.loads((OUT/path).read_bytes())
        assets=[{'name': a['name'], 'bytes':a['size'], 'url':a['browser_download_url'],
                 'digest':a.get('digest')} for a in obj.get('assets', [])
                if any(s in a['name'].lower() for s in ['orangepi5_', 'rock-5b_'])]
        (OUT/'official-image-candidates.json').write_text(json.dumps({
            'repository':'armbian/'+repo, 'tag':obj.get('tag_name'),
            'release_url':obj.get('html_url'), 'assets':assets},indent=2)+'\n')
    except Exception as error:
        records.append({'repository':repo,'error':str(error)})
result={'date':'2026-10-29','build_commit':PIN,
        'scope':'Official build integration and release metadata; no target hardware validation',
        'files':records}
(OUT/'manifest.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'commit':PIN,'files':len(records),
                  'errors':[r for r in records if 'error' in r],
                  'panthor_files':[p for p in paths if 'panthor' in p.lower()]},indent=2))
