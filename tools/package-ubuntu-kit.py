"""Build and read-back-verify the offline Ubuntu 20.04 collection kit."""
from pathlib import Path
import hashlib
import json
import zipfile

project = Path(__file__).resolve().parent.parent
files = {
    'run-collect.sh': project / 'tools/run-collect.sh',
    'collect-hardware.sh': project / 'tools/collect-hardware.sh',
    'prepare-ubuntu-tools.sh': project / 'tools/prepare-ubuntu-tools.sh',
    'README.md': project / 'docs/ubuntu-20.04-ready.md',
}
output = project / 'outputs/F8-PRO-Ubuntu20.04-kit.zip'
output.parent.mkdir(exist_ok=True)
manifest = {}
with zipfile.ZipFile(output, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
    for name, path in files.items():
        payload = path.read_bytes()
        if name.endswith('.sh'):
            assert b'\r' not in payload, f'{name} must use Linux LF line endings'
        info = zipfile.ZipInfo(name)
        info.create_system = 3
        info.external_attr = (0o100755 if name.endswith('.sh') else 0o100644) << 16
        archive.writestr(info, payload, compress_type=zipfile.ZIP_DEFLATED)
        manifest[name] = {'sha256': hashlib.sha256(payload).hexdigest(), 'bytes': len(payload)}
    archive.writestr('manifest.json', json.dumps(manifest, indent=2) + '\n')
with zipfile.ZipFile(output) as archive:
    assert archive.testzip() is None
    for name, path in files.items():
        assert archive.read(name) == path.read_bytes()
sha256 = hashlib.sha256(output.read_bytes()).hexdigest()
output.with_suffix('.zip.sha256').write_text(sha256 + '  ' + output.name + '\n', encoding='ascii')
print('Verified:', output)
print('SHA-256:', sha256)
