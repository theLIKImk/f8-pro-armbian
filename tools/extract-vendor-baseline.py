"""Recover original boot assets and Linux metadata without mounting source images.

The tar is a research bundle, not an overlay to install blindly on Arch Linux.
No source image or device is written. Requires only Python's standard library.
"""
import argparse
import hashlib
import io
import json
from pathlib import Path
import re
import struct
import tarfile

from inspect_images import Ext4, Package, fdt


def digest_file(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def recover(source, output, expected_sha256):
    source = source.resolve()
    output = output.resolve()
    if output.exists():
        raise ValueError('Output already exists; choose a new directory')
    source_hash = digest_file(source)
    if source_hash != expected_sha256.lower():
        raise ValueError('Source SHA-256 does not match recorded original')
    pkg = Package(source)
    try:
        fs = Ext4(pkg, 'rootfs')
        output.mkdir(parents=True)
        assets = output / 'boot-assets'
        assets.mkdir()
        report = {'source': str(source), 'source_sha256': source_hash,
                  'purpose': 'Original vendor diagnostic baseline; not a flashable Arch image',
                  'boot_assets': [], 'rootfs_entries': []}
        for name in ('bootloader', 'parameter', 'package-file', 'uboot', 'misc', 'boot', 'recovery'):
            payload = pkg.read(name)
            path = assets / Path(pkg.entries[name]['path']).name
            path.write_bytes(payload)
            report['boot_assets'].append({**pkg.entries[name], 'name': name,
                                         'file': path.relative_to(output).as_posix(),
                                         'sha256': hashlib.sha256(payload).hexdigest()})

        boot = pkg.read('boot')
        nodes = fdt(boot)
        kernel = b''
        for name in ('kernel', 'fdt', 'resource'):
            props = nodes['/images/' + name]
            position = int.from_bytes(props['data-position'], 'big')
            size = int.from_bytes(props['data-size'], 'big')
            if position + size > len(boot):
                raise ValueError('FIT payload outside boot image')
            payload = boot[position:position + size]
            hash_props = nodes['/images/' + name + '/hash']
            if hash_props['algo'] != b'sha256\0':
                raise ValueError('Unsupported FIT hash')
            if hashlib.sha256(payload).digest() != hash_props['value']:
                raise ValueError('FIT payload hash mismatch: ' + name)
            suffix = {'kernel': 'Image', 'fdt': 'board.dtb', 'resource': 'resource.img'}[name]
            (assets / suffix).write_bytes(payload)
            report['boot_assets'].append({'name': 'fit-' + name,
                                         'file': 'boot-assets/' + suffix, 'size': size,
                                         'sha256': hashlib.sha256(payload).hexdigest()})
            if name == 'kernel':
                kernel = payload
        banner = re.search(rb'Linux version [^\x00\n]+', kernel)
        report['kernel_banner'] = banner.group().decode('utf-8', 'replace') if banner else None
        # Preserve Linux inode metadata in tar; never materialize Linux symlinks on NTFS.
        roots = ('/etc/firmware', '/usr/lib/firmware', '/lib/firmware', '/vendor/etc/firmware',
                 '/usr/lib/modules', '/lib/modules', '/vendor/lib/modules', '/etc/iqfiles')
        files = list(fs.walk())
        report['rootfs_scanned_entries'] = len(files)
        hardlinks = {}
        archive = output / 'vendor-hardware.tar'
        with tarfile.open(archive, 'w', format=tarfile.PAX_FORMAT) as tar:
            for path, ino, kind in sorted(files):
                if not any(path == root or path.startswith(root + '/') for root in roots):
                    continue
                inode = fs.inode(ino)
                mode, uid = struct.unpack_from('<HH', inode)
                gid = struct.unpack_from('<H', inode, 24)[0]
                uid |= struct.unpack_from('<H', inode, 120)[0] << 16
                gid |= struct.unpack_from('<H', inode, 122)[0] << 16
                entry = tarfile.TarInfo(path.lstrip('/'))
                entry.mode, entry.uid, entry.gid = mode & 0o7777, uid, gid
                entry.mtime = struct.unpack_from('<I', inode, 16)[0]
                metadata = {'path': path, 'inode': ino, 'mode': oct(entry.mode),
                            'uid': uid, 'gid': gid, 'kind': kind}
                content = None
                if kind == 2:
                    entry.type = tarfile.DIRTYPE
                elif kind == 7:
                    entry.type = tarfile.SYMTYPE
                    entry.linkname = fs.content(ino).decode('utf-8')
                    metadata['target'] = entry.linkname
                elif kind == 1:
                    payload = fs.content(ino, limit=256 * 1024 * 1024)
                    metadata['size'] = len(payload)
                    metadata['sha256'] = hashlib.sha256(payload).hexdigest()
                    if ino in hardlinks:
                        entry.type = tarfile.LNKTYPE
                        entry.linkname = hardlinks[ino]
                        metadata['target'] = '/' + entry.linkname
                    else:
                        hardlinks[ino] = entry.name
                        entry.size = len(payload)
                        content = io.BytesIO(payload)
                else:
                    raise ValueError('Unsupported selected inode type: ' + path)
                tar.addfile(entry, content)
                report['rootfs_entries'].append(metadata)
        # Read every regular payload back and compare to its original source hash.
        by_path = {entry['path'].lstrip('/'): entry for entry in report['rootfs_entries']}
        with tarfile.open(archive) as tar:
            members = tar.getmembers()
            if len(members) != len(by_path):
                raise ValueError('Archive entry count mismatch')
            for member in members:
                metadata = by_path[member.name]
                if member.isfile() or member.islnk():
                    stream = tar.extractfile(member)
                    if hashlib.file_digest(stream, 'sha256').hexdigest() != metadata['sha256']:
                        raise ValueError('Archive read-back mismatch: ' + member.name)
        report['archive'] = {'file': archive.name, 'size': archive.stat().st_size,
                             'sha256': digest_file(archive), 'readback_verified': True}
        report['selected_roots'] = list(roots)
        (output / 'manifest.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        print(json.dumps({key: report[key] for key in ('kernel_banner', 'rootfs_scanned_entries', 'archive')}, indent=2))
        print('Recovered entries:', len(report['rootfs_entries']))
    finally:
        pkg.f.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--sha256', required=True, help='Expected original update image SHA-256')
    args = parser.parse_args()
    recover(args.source, args.output, args.sha256)
