"""Extract only private GPU runtime files from the original factory rootfs.

Verifies the original package's MD5 for each payload and records SHA-256.
Never executes the blobs or replaces system libraries.
"""
import hashlib
import importlib.util
import json
from pathlib import Path, PurePosixPath
import posixpath
import struct

PROJECT = Path(__file__).resolve().parent.parent


def main():
    spec = importlib.util.spec_from_file_location('images', PROJECT/'tools/inspect_images.py')
    images = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(images)
    package = images.Package(PROJECT.parent/'update-UBUNTU20.04.img')
    fs = images.Ext4(package, 'rootfs')
    info = '/var/lib/dpkg/info/libmali-valhall-g610-g13p0-x11-wayland-gbm.md5sums'
    sums = dict((row.split()[1], row.split()[0]) for row in fs.content(fs.lookup(info)).decode().splitlines())
    directory = PROJECT/'vendor/ubuntu-5.10.160/gpu'
    directory.mkdir(exist_ok=True)
    sources = {
        'libmali.so.1.9.0': '/usr/lib/aarch64-linux-gnu/libmali.so.1.9.0',
        'libmali_hook.so.1.9.0': '/usr/lib/aarch64-linux-gnu/libmali_hook.so.1.9.0',
        'libEGL.so.1': '/usr/lib/aarch64-linux-gnu/mali/libEGL.so.1',
        'libGLESv2.so.2': '/usr/lib/aarch64-linux-gnu/mali/libGLESv2.so.2',
        'libgbm.so.1': '/usr/lib/aarch64-linux-gnu/mali/libgbm.so.1',
        'libwayland-egl.so.1': '/usr/lib/aarch64-linux-gnu/mali/libwayland-egl.so.1',
        'copyright': '/usr/share/doc/libmali-valhall-g610-g13p0-x11-wayland-gbm/copyright',
    }
    records = []
    for target, source in sources.items():
        actual = source
        for _ in range(16):
            ino = fs.lookup(actual)
            mode = struct.unpack_from('<H', fs.inode(ino))[0]
            if mode & 0xf000 != 0xa000:
                break
            link = fs.content(ino).decode()
            actual = posixpath.normpath(link if link.startswith('/') else str(PurePosixPath(actual).parent/link))
        else:
            raise ValueError('Factory library symlink loop')
        data = fs.content(ino, limit=256*1024**2)
        expected = sums.get(actual.lstrip('/'))
        if expected is None or hashlib.md5(data).hexdigest() != expected:
            raise ValueError('Factory package payload checksum mismatch')
        if target != 'copyright' and data[:4] != b'\x7fELF':
            raise ValueError('GPU runtime payload is not ELF')
        (directory/target).write_bytes(data)
        records.append({'file': target, 'source': source, 'resolved_source': actual,
                        'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest(),
                        'factory_dpkg_md5_matched': True})
    report = {'source_image': 'update-UBUNTU20.04.img', 'files': records,
              'installed_on_arch': False, 'arch_render_tested': False,
              'system_graphics_libraries_replaced': False}
    (PROJECT/'analysis/vendor-userspace/gpu-library.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({'verified_files': len(records), 'total_bytes': sum(r['bytes'] for r in records),
                      'installed_on_arch': False}))


if __name__ == '__main__':
    main()
