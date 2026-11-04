"""Download exact official kernel packages against exported signed APT hashes."""
import concurrent.futures
import hashlib
import json
from pathlib import Path
import urllib.request

BASE = Path(__file__).resolve().parents[1]
out = BASE / 'downloads/armbian/packages'
out.mkdir(parents=True, exist_ok=True)
text = (BASE / 'analysis/armbian/repository/kernel-packages.deb822').read_text()
records = []
for block in text.strip().split('\n\n'):
    record = dict(line.split(': ', 1) for line in block.splitlines() if ': ' in line and not line.startswith(' '))
    assert record['Version'] == '26.8.3' and record['Architecture'] == 'arm64'
    records.append(record)


def fetch(record):
    path = out / Path(record['Filename']).name
    url = 'https://apt.armbian.com/' + record['Filename']
    if not path.is_file():
        part = path.with_suffix('.part')
        failures = []
        for mirror in ['https://apt.armbian.com/', 'https://mirrors.qlu.edu.cn/armbian/',
                       'https://mirrors.tuna.tsinghua.edu.cn/armbian/']:
            try:
                url = mirror + record['Filename']
                with urllib.request.urlopen(url, timeout=60) as response, part.open('wb') as stream:
                    while data := response.read(1024 * 256):
                        stream.write(data)
                break
            except Exception as error:
                failures.append(str(error))
        else:
            raise RuntimeError(f'All mirrors failed: {failures}')
        assert part.stat().st_size == int(record['Size'])
        assert hashlib.file_digest(part.open('rb'), 'sha256').hexdigest() == record['SHA256']
        part.replace(path)
    assert hashlib.file_digest(path.open('rb'), 'sha256').hexdigest() == record['SHA256']
    return {'package': record['Package'], 'version': record['Version'], 'url': url,
            'file': str(path.relative_to(BASE)), 'bytes': path.stat().st_size, 'sha256': record['SHA256']}


with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
    result = list(pool.map(fetch, records))
(BASE / 'analysis/armbian/repository/downloaded-kernel-packages.json').write_text(json.dumps(result, indent=2) + '\n')
print('Verified all 3 official kernel packages against signed APT SHA256 values')
