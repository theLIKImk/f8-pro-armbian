"""Fetch only rk3588s.dtsi and its transitive C/DTS include files at the pinned commit."""
import concurrent.futures
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import urllib.request

BASE = Path(__file__).resolve().parents[1]
OUT = BASE / 'analysis/armbian/source-audit'
manifest = json.loads((OUT / 'manifest.json').read_text())
sha = manifest['pins']['linux-rockchip']
root = OUT / 'linux-rockchip'
records = {r['path']: r for r in manifest['files'] if r['repository'] == 'linux-rockchip'}
pending = {'arch/arm64/boot/dts/rockchip/rk3588s.dtsi'}
visited = set()


def fetch(path):
    url = f'https://raw.githubusercontent.com/armbian/linux-rockchip/{sha}/{path}'
    dst = root / path
    prior = records.get(path)
    if dst.is_file() and prior and prior.get('sha256') == hashlib.sha256(dst.read_bytes()).hexdigest():
        data = dst.read_bytes()
    else:
        req = urllib.request.Request(url, headers={'User-Agent': 'F8-PRO-DT-audit'})
        with urllib.request.urlopen(req, timeout=35) as response:
            data = response.read()
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(data)
    record = {'repository': 'linux-rockchip', 'commit': sha, 'path': path, 'url': url,
              'status': 'present', 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}
    includes = set()
    for delim, name in re.findall(r'^\s*#include\s*([<"])([^>"\n]+)[>"]', data.decode(), re.M):
        child = PurePosixPath('include') / name if delim == '<' else PurePosixPath(path).parent / name
        if '..' in child.parts:
            raise ValueError(f'Unexpected parent traversal: {child}')
        includes.add(str(child))
    return record, includes


while pending:
    batch = sorted(pending - visited)
    if not batch:
        break
    if len(visited) + len(batch) > 200:
        raise ValueError('Unexpected include closure size')
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        results = list(pool.map(fetch, batch))
    pending = set()
    for record, children in results:
        records[record['path']] = record
        visited.add(record['path'])
        pending.update(children - visited)
manifest['files'] = [r for r in manifest['files'] if r['repository'] != 'linux-rockchip'] + list(records.values())
(OUT / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
(OUT / 'dt-closure.json').write_text(json.dumps({'commit': sha, 'files': sorted(visited)}, indent=2) + '\n')
print(f'Verified {len(visited)} SoC DTS/header inputs at {sha}')
