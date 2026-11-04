"""Fetch candidate board inputs from the previously pinned official kernel commit."""
import concurrent.futures
import hashlib
import json
from pathlib import Path
import urllib.error
import urllib.request

BASE = Path(__file__).resolve().parents[1]
OUT = BASE / 'analysis/armbian/source-audit'


def read(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'F8-PRO-board-audit'})
    with urllib.request.urlopen(req, timeout=35) as response:
        return response.read()


def main():
    manifest = json.loads((OUT / 'manifest.json').read_text())
    sha = manifest['pins']['linux-rockchip']
    directory = 'arch/arm64/boot/dts/rockchip'
    entries = json.loads(read(f'https://api.github.com/repos/armbian/linux-rockchip/contents/{directory}?ref={sha}'))
    (OUT / 'rockchip-dts-directory.json').write_text(json.dumps(entries, indent=2) + '\n')
    candidates = [e['path'] for e in entries if '3588' in e['name'] and ('tablet' in e['name'] or 'f12' in e['name'])]
    print('Board candidates:', candidates)
    paths = candidates + [
        'drivers/input/touchscreen/gsl3673.c',
        'drivers/input/touchscreen/gsl3673.h',
        'drivers/input/touchscreen/gslx680_pad.h',
        'drivers/input/sensors/sensor-dev.c',
        'drivers/input/sensors/Kconfig',
        'drivers/input/sensors/Makefile',
        'include/linux/sensor-dev.h',
        'arch/arm64/boot/dts/rockchip/rk3588s.dtsi',
        'arch/arm64/boot/dts/rockchip/rk3588s-tablet.dtsi']

    def fetch(path):
        url = f'https://raw.githubusercontent.com/armbian/linux-rockchip/{sha}/{path}'
        record = {'repository': 'linux-rockchip', 'commit': sha, 'path': path, 'url': url}
        try:
            data = read(url)
            dst = OUT / 'linux-rockchip' / path
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_bytes(data)
            record.update(status='present', bytes=len(data), sha256=hashlib.sha256(data).hexdigest())
        except urllib.error.HTTPError as e:
            record.update(status='path_not_found' if e.code == 404 else 'http_error', code=e.code)
        except Exception as e:
            record.update(status='fetch_error', error=str(e))
        return record

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(fetch, paths))
    manifest['files'] = [r for r in manifest['files'] if r['path'] not in paths] + results
    (OUT / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    for r in results:
        print(r['status'], r['path'])


if __name__ == '__main__':
    main()
