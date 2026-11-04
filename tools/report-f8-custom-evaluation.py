"""Bind checked custom-ABI artifacts into a non-deployable evaluation manifest."""
import hashlib
import json
from pathlib import Path

P = Path(__file__).resolve().parents[1]
release = '6.1.172-f8-pro-armbian-eval'
kernel = json.loads((P / 'analysis/armbian/kernel-build/verified-evaluation-image.json').read_text())
modules = json.loads((P / 'analysis/armbian/kernel-build/verified-custom-modules.json').read_text())
root = json.loads((P / 'analysis/armbian/userspace/verified-wayland-squashfs.json').read_text())
init = json.loads((P / 'analysis/armbian/initramfs/custom/verified-initramfs.json').read_text())
assert kernel['release'] == modules['release'] == root['module_release'] == init['release'] == release
assert root['sha256'] == init['rootfs_sha256']
image_info = next(item for item in kernel['files'] if item['name'] == 'Image')
artifacts = []
for role, relative, expected in [
    ('kernel', 'outputs/armbian/evaluation-kernel/Image', image_info['sha256']),
    ('modules', 'outputs/armbian/evaluation-kernel/modules-' + release + '.tar.gz', modules['archive_sha256']),
    ('desktop-rootfs', 'outputs/armbian/evaluation-wayland/rootfs.squashfs', root['sha256']),
    ('initramfs', 'outputs/armbian/evaluation-initramfs-custom/initramfs-6.1.172-custom-DO-NOT-BOOT.cpio.gz', init['archive_sha256']),
]:
    path = P / relative
    with path.open('rb') as stream:
        digest = hashlib.file_digest(stream, 'sha256').hexdigest()
    assert digest == expected, role
    artifacts.append({'role': role, 'project_relative_path': relative, 'bytes': path.stat().st_size, 'sha256': digest})
result = {'release': release, 'scope': 'Offline matching artifact set; DO NOT BOOT/FLASH',
          'artifacts': artifacts, 'raw_kernel_plus_initramfs_bytes': init['image_plus_initramfs_bytes'],
          'boot_partition_bytes': init['boot_partition_bytes'], 'includes_fit_metadata_or_dtb': False,
          'bootable_board_image': False, 'hardware_tests_performed': False,
          'pending': ['Complete board DT and loader memory fixup validation',
                      'Charging/USB-C and touch adaptation', 'GPU/display and Wayland input tests',
                      'First-user and persistent state provisioning', 'Boot packaging and rollback review']}
(P / 'outputs/armbian/evaluation-custom-set.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
