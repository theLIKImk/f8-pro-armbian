"""Fetch a commit-specific source archive and verify audited files inside it."""
import hashlib
import json
from pathlib import Path
import tarfile
import urllib.request

BASE = Path(__file__).resolve().parents[1]
audit = json.loads((BASE / 'analysis/armbian/source-audit/manifest.json').read_text())
sha = audit['pins']['linux-rockchip']
dest = BASE / 'downloads/armbian'
dest.mkdir(parents=True, exist_ok=True)
archive = dest / f'linux-rockchip-{sha}.tar.gz'
url = f'https://codeload.github.com/armbian/linux-rockchip/tar.gz/{sha}'
if not archive.is_file():
    partial = archive.with_suffix('.part')
    with urllib.request.urlopen(url, timeout=60) as response, partial.open('wb') as stream:
        while data := response.read(1024 * 1024):
            stream.write(data)
    partial.replace(archive)
verified = []
with tarfile.open(archive) as tar:
    prefix = f'linux-rockchip-{sha}/'
    for record in audit['files']:
        if record['repository'] != 'linux-rockchip' or record['status'] != 'present':
            continue
        data = tar.extractfile(prefix + record['path']).read()
        assert hashlib.sha256(data).hexdigest() == record['sha256'], record['path']
        verified.append(record['path'])
result = {'url': url, 'commit': sha, 'archive': str(archive.relative_to(BASE)),
          'bytes': archive.stat().st_size, 'sha256': hashlib.file_digest(archive.open('rb'), 'sha256').hexdigest(),
          'audited_files_verified': verified, 'scope': 'Official HTTPS archive plus audited file comparisons; no kernel build yet'}
(BASE / 'analysis/armbian/kernel-archive.json').write_text(json.dumps(result, indent=2) + '\n')
print(f'Archive verified: {result["bytes"]} bytes, {len(verified)} audited files')
