"""Read-only check of an F8-PRO image against its intended partition.

This never connects to a device and cannot verify the selection in RKDevTool.
It rejects a rootfs image selected for boot before hashing the large file.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys

PARTITIONS = {
    'boot': (0x8000, 64*1024**2, 'fit'),
    'recovery': (0x28000, 128*1024**2, 'fit'),
    'rootfs': (0x78000, 246960619520, 'ext4'),
}
KNOWN = {
    'cbd14e32ef05d9571745ba8b790c694f7a81112e37783a4cf873c7d0c918ef46': ('boot', 49460108, 'full-performance-p3-gpu1000mhz-short-load-and-cpu-gpu-cold-boot-auto-restore-verified-requires-root-assets'),
    'a3a23fd7ea637cff25e333f7c52d212a9a9310f8b3ebb0b54a25a700301aa76e': ('boot', 49460132, 'cpu-p2a-cold-boot-manual-driver-and-816-1008-1200mhz-short-tests-verified'),
    'aaabb0ff25cbc339f6a233a0fed5939fd96c228328b315a0039f66e546b5d7b3': ('boot', 49460040, 'gpu-p1-cold-boot-and-short-terrain-load-verified-200-300-400mhz'),
    '2a4901174382cbb8e0387f8de0220c8bebfff2fb830ca7d6aac5dd7794cb75dd': ('boot', 49459328, 'f8-r1a-first-run-helper-and-guarded-online-root-grow-cold-boot-unverified'),
    '444c80ddf7220537e3a40595e08efb191599dab096393c101b0f6ba4e6d98dde': ('rootfs', 12884901888, 'f8-armbian-r1-first-run-fsck-readback-verified-cold-boot-unverified'),
    'fbbfa1ece55b3c62decbd10ae9c2ac98ed5d717dd5f8b941c49004deb6c0903a': ('boot', 49453800, 'camera-c4-official-c2-kernel-async-waits-early-sensors-cold-boot-unverified'),
    '41b1f3f84f23107ee0de68a567406fa797de5436b65de6ab554acc538bb7247f': ('boot', 49453272, 'camera-c2-shared-mclk-owner-late-isp-start-candidate'),
    '1b39e4e0f49c2085081617f0ef8a1b087886ae3ef6af84330c01f4125dd682c7': ('boot', 49446208, 'motion-s1-boot-six-axis-readable-needs-root-180-degree-matrix-fix'),
    'de2d364e8163914e7996332d1551c07bf9e50316c6b1bf0f3d22dfd61dab6cb1': ('boot', 49445912, 'bluetooth-bt1-boot-controller-and-user-scan-verified'),
    '9044ece30ff5806f975f9030b49dab8f8bed38226bce9385381dee5708c5e237': ('boot', 49445856, 'native-usb-u5-usb2-only-pipe-status-candidate'),
    'f3179f09462038dc9e2c60bce6d00fc149aa3c0e693aa8af41c71f756b771fba': ('boot', 49445820, 'native-usb-u4r1-physical-phy-child-order-candidate'),
    '5ccccc72e7536d2825279961b7f434be018aeeabfae8aaf13b0cb20082124e46': ('boot', 49445036, 'native-usb-u3-tcpm-role-graph-candidate'),
    '891f3ee912dda91aad9d6a795b06f5e2c611e6488cffab6840e99bacc9be3b5f': ('boot', 49445072, 'native-usb-u2-unified-dt-deferred-module-candidate'),
    '831ca9b5eb6595e2e3b91353c26964aeb759381c822d83ef09200096c6126df3': ('boot', 49426624, 'native-audio-a3-cold-boot-and-speaker-short-tone-verified'),
    'bd7277d09b7928ef554960986ab14076292a57a247aac59d13bd57bd2f7376ec': ('boot', 49426612, 'native-audio-a2-backlight-mux-fix-candidate'),
    '7ed3dab57aa6eb84ddc13e50b1d58104815962a5c18e7d7f09e46f876a76f2e7': ('boot', 49426544, 'native-audio-a1-candidate-not-hardware-verified'),
    '283c136d299e47e1b6b119a8c8838f513ce81668dedfd6ff99ab3a75961c2c8b': ('boot', 49426564, 'native-desktop-t1r2-verified'),
    '9fda4aca3978e39a8bc3b185596c7ff824ce66fd50ce9862062e6cc6595eecd4': ('rootfs', 12884901888, 'armbian-native-desktop-t1'),
    '3b488ca72b247146d8a8d79fbf1e3481860852fb691707f84fb4abd4606a2c4c': ('boot', 49425676, 'armbian-native-desktop-t1'),
    '8e4d8d7fd7d4135b3774c0ab9b4e18f776045776dfe91795d51ce512fc0e71cf': ('rootfs', 17179869184, 'original-file-level-rollback-20261030'),
    '7e51e71f7ec7439357e5ea2fbb97118715fe5fcf10401b638609df33567b1dd1': ('boot', 67108864, 'original-boot-full-partition-backup'),
    '018d139a2bfe741e73db941583907293c52f2509a2328c738720fe6d849c1f83': ('boot', 40221184, 'factory-boot'),
    '369945d2f6e8f10bb50bd2ab0d9477a7823b36831d815def788c3bd08ce5f875': ('boot', 48764620, 'usb-bootlog'),
    'b570363e1f2ad7b797db5514970835f44b20d7101b45432b28d26c70547dd641': ('boot', 48764948, 'usb-bootlog-probe'),
    'be75e3e8604a07c4c208a09f57947923c08e99ce1e4b494b688b3ddb14daa556': ('boot', 48765560, 'usb-arch-handoff'),
    '2e392273f1d5b350987fd40bf68ee7bc10084cbd7f16f22fc5c3bf0e66b82b54': ('boot', 48767416, 'wifi-mac-fix'),
    '5cad7f68a95869f97bbdc6c9539960a7d7812ba78b507510282a196966019fdd': ('boot', 48300192, 'normal-boot'),
    '49d34ae55996490f271e279af466736bea15af7dea806cbbcdbf850d89d822f5': ('recovery', 48372224, 'factory-recovery'),
    '0f8b7d7d7aa68390bebe6309135d61b61b67cde4cbe73d28ebb3b4f115d67f61': ('rootfs', 2147483648, 'screen-diagnostic'),
    '5e5d911e412f83b67af49bdd3151695a4281dabbfa5af5d6f3ea8a233634bfaf': ('rootfs', 8589934592, 'wifi-test'),
}


def check(partition, image):
    image = Path(image).resolve(strict=True)
    if not image.is_file():
        raise ValueError('Image is not a regular file')
    start, capacity, kind = PARTITIONS[partition]
    size = image.stat().st_size
    if size > capacity:
        raise ValueError(f'File is {size} bytes; {partition} holds only {capacity} bytes. Do not write it.')
    with image.open('rb') as f:
        header = f.read(1082)
        if kind == 'fit' and header[:4] != bytes.fromhex('d00dfeed'):
            raise ValueError('Expected a FIT boot/recovery image; this file has a different header')
        if kind == 'ext4' and header[1080:1082] != bytes.fromhex('53ef'):
            raise ValueError('Expected a raw ext4 rootfs image')
        f.seek(0)
        checksum = hashlib.sha256()
        count, report = 0, 1024**3
        while chunk := f.read(8*1024**2):
            checksum.update(chunk)
            count += len(chunk)
            if count >= report:
                print(json.dumps({'checked_mib': count//1024**2}), file=sys.stderr, flush=True)
                report += 1024**3
        digest = checksum.hexdigest()
    expected = KNOWN.get(digest)
    if not expected or expected[:2] != (partition, size):
        raise ValueError('Image hash/size is not an approved local artifact for this partition')
    return {'result': 'PASS', 'image': str(image), 'bytes': size, 'sha256': digest,
            'partition': partition, 'expected_start_lba': f'0x{start:08x}',
            'variant': expected[2], 'device_partition_table_verified': False,
            'rkdevtool_selected_file_verified': False, 'device_written': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--partition', required=True, choices=PARTITIONS)
    parser.add_argument('--image', required=True, type=Path)
    args = parser.parse_args()
    try:
        result = check(args.partition, args.image)
    except (ValueError, OSError) as e:
        print('FAIL: '+str(e), file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=True, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
