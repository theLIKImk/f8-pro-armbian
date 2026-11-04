"""Package verified factory GPU libraries only for an isolated /opt test prefix."""
import hashlib
import io
import json
from pathlib import Path
import re
import tarfile

PROJECT = Path(__file__).resolve().parent.parent


def main():
    manifest = json.loads((PROJECT/'analysis/vendor-userspace/gpu-library.json').read_text())
    output = PROJECT/'outputs/F8-PRO-private-gpu-g13p0.tar.gz'
    output.parent.mkdir(exist_ok=True)
    if output.exists():
        raise RuntimeError('Kit exists; refusing overwrite')
    temporary = output.with_name(output.name+'.partial')
    if temporary.exists():
        raise RuntimeError('Incomplete kit exists; inspect it before retrying')
    with tarfile.open(temporary, 'w:gz') as archive:
        def add(name, data, mode=0o644):
            info = tarfile.TarInfo(name)
            info.mode, info.size = mode, len(data)
            archive.addfile(info, io.BytesIO(data))
        for record in manifest['files']:
            name = record['file']
            if name != 'copyright' and not re.fullmatch(r'lib[A-Za-z0-9_-]+\.so(?:\.[0-9]+)+', name):
                raise ValueError('Unexpected runtime filename')
            data = (PROJECT/'vendor/ubuntu-5.10.160/gpu'/name).read_bytes()
            if hashlib.sha256(data).hexdigest() != record['sha256']:
                raise ValueError('GPU library changed after factory verification')
            add('copyright' if name == 'copyright' else 'lib/'+name, data)
        for name, target in [('libmali.so.1', 'libmali.so.1.9.0'), ('libmali_hook.so.1', 'libmali_hook.so.1.9.0')]:
            info = tarfile.TarInfo('lib/'+name)
            info.type, info.linkname, info.mode = tarfile.SYMTYPE, target, 0o777
            archive.addfile(info)
        add('probe-gpu-context.py', (PROJECT/'tools/probe-gpu-context.py').read_bytes().replace(b'\r\n', b'\n'))
        add('source-manifest.json', json.dumps(manifest, indent=2).encode())
    temporary.replace(output)
    with output.open('rb') as stream:
        digest = hashlib.file_digest(stream, 'sha256').hexdigest()
    record = {'file': output.name, 'sha256': digest, 'bytes': output.stat().st_size,
              'target_prefix': '/opt/f8-pro/vendor-gpu-g13p0-20261028',
              'changes_global_graphics_configuration': False, 'render_tested': False}
    (PROJECT/'analysis/vendor-userspace/private-gpu-kit.json').write_text(json.dumps(record, indent=2)+'\n')
    print(json.dumps(record))


if __name__ == '__main__':
    main()
