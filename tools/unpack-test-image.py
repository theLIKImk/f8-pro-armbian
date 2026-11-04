"""Prepare a verified raw partition image in the private Windows export folder."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import shutil
import tempfile


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def unpack(directory):
    manifest = json.loads((directory / 'manifest.json').read_text(encoding='utf-8'))
    if not manifest.get('critical_image_contents_verified'):
        raise ValueError('Complete image content verification first')
    name = 'f8-pro-arch-' + manifest['variant'] + '.img'
    if manifest['variant'] not in ('pending-wifi', 'wifi-test'):
        raise ValueError('Unexpected image variant')
    source, target = directory / (name + '.gz'), directory / name
    if target.exists():
        if target.is_symlink() or digest(target) != manifest['image_sha256']:
            raise ValueError('An existing raw image differs; refusing to overwrite it')
    else:
        if digest(source) != manifest['gzip_sha256']:
            raise ValueError('Compressed input SHA-256 mismatch')
        expected = manifest['partition_image_bytes']
        if shutil.disk_usage(directory).free < expected + 128 * 1024 * 1024:
            raise ValueError('Not enough free space for the raw partition image')
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(prefix=name + '.', suffix='.part', dir=directory, delete=False) as output:
                temporary = Path(output.name)
                computed, total = hashlib.sha256(), 0
                with gzip.open(source, 'rb') as stream:
                    while True:
                        chunk = stream.read(8 * 1024 * 1024)
                        if not chunk:
                            break
                        total += len(chunk)
                        if total > expected:
                            raise ValueError('Unexpected expanded size')
                        computed.update(chunk)
                        output.write(chunk)
                if total != expected or computed.hexdigest() != manifest['image_sha256']:
                    raise ValueError('Raw image size or SHA-256 mismatch')
            temporary.rename(target)
            temporary = None
        finally:
            if temporary is not None and temporary.is_file():
                temporary.unlink()
    manifest['windows_raw_image_verified'] = True
    manifest['windows_raw_image_name'] = target.name
    (directory / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    sums = directory / 'SHA256SUMS'
    rows = [line for line in sums.read_text(encoding='utf-8').splitlines() if not line.endswith('  ' + target.name)]
    sums.write_text('\n'.join(rows + [manifest['image_sha256'] + '  ' + target.name]) + '\n', encoding='ascii')
    print('Raw image prepared and verified:', target)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    args = parser.parse_args()
    unpack(args.directory)
