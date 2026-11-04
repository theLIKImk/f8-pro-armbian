"""Build a separate, unflashed diagnostic rootfs from the sealed test candidate.

Run as root inside the existing WSL build distro. Never alters the original
candidate, existing images, client key or physical device.
"""
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

BASE = Path('/var/tmp/f8-pro-archlinux-20261027')
SOURCE = BASE / 'rootfs-vendor-staging'
ROOT = BASE / 'rootfs-boot-diagnostic-20261028'
EXPORT = BASE / 'exports/boot-diagnostic'
BINARY = BASE / 'diagnostic-build/early-init'
SIZE = 2 * 1024**3


def run(argv):
    result = subprocess.run(argv, capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError(f'{argv[0]} failed: {result.stderr[-1200:]}')
    return result.stdout


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    os.umask(0o077)
    if os.getuid() != 0 or not (SOURCE / 'etc/arch-release').is_file():
        raise RuntimeError('Run as root in the existing Linux build environment')
    if ROOT.exists() or EXPORT.exists():
        raise RuntimeError('Diagnostic output exists; do not overwrite it')
    if not BINARY.is_file():
        raise RuntimeError('Compile and self-test the static ARM64 diagnostic first')
    run(['qemu-aarch64-static', str(BINARY), '--self-test'])
    for row in Path('/proc/self/mountinfo').read_text().splitlines():
        mountpoint = row.split()[4]
        if mountpoint == str(SOURCE) or mountpoint.startswith(str(SOURCE) + '/'):
            raise RuntimeError('Candidate has mounted runtime directories')
    if (SOURCE / 'etc/machine-id').read_bytes():
        raise RuntimeError('Source machine-id is not empty')
    if list((SOURCE / 'etc/ssh').glob('ssh_host_*_key')):
        raise RuntimeError('Source contains host private keys')
    if (SOURCE / 'etc/pacman.d/gnupg/private-keys-v1.d').exists():
        raise RuntimeError('Source contains a build signing key directory')
    profile = SOURCE / 'etc/NetworkManager/system-connections/f8-pro-test-wifi.nmconnection'
    if not profile.is_file() or profile.stat().st_mode & 0o777 != 0o600:
        raise RuntimeError('Verified private Wi-Fi profile missing')
    run(['cp', '-a', '--reflink=auto', str(SOURCE), str(ROOT)])
    print('Cloned sealed test candidate; original preserved', flush=True)
    init = ROOT / 'usr/bin/init'
    if not init.is_symlink() or os.readlink(init) != '../lib/systemd/systemd':
        raise RuntimeError('Unexpected init layout; refusing replacement')
    import shutil
    target = ROOT / 'usr/libexec/f8-pro/early-init'
    shutil.copyfile(BINARY, target)
    target.chmod(0o755)
    init.unlink()
    init.symlink_to('../libexec/f8-pro/early-init')
    EXPORT.mkdir(mode=0o700)
    image = EXPORT / 'f8-pro-arch-boot-diagnostic.img'
    with image.open('xb') as stream:
        stream.truncate(SIZE)
    run(['mke2fs', '-F', '-t', 'ext4', '-b', '4096', '-m', '1', '-L', 'F8_ARCH_DIAG',
         '-O', '^orphan_file,^metadata_csum_seed',
         '-E', 'lazy_itable_init=0,lazy_journal_init=0,root_owner=0:0',
         '-d', str(ROOT), str(image)])
    print('Diagnostic filesystem populated', flush=True)
    check = run(['e2fsck', '-f', '-n', str(image)])
    (EXPORT / 'e2fsck.txt').write_text(check)

    def debug(command):
        return run(['debugfs', '-R', command, str(image)])

    stats = debug('stat /etc/NetworkManager/system-connections/f8-pro-test-wifi.nmconnection')
    if not re.search(r'Mode:\s+0600', stats) or not re.search(r'User:\s+0\s+Group:\s+0', stats):
        raise RuntimeError('Image Wi-Fi profile permissions invalid')
    # Compare secret values only in memory, never print or export their contents.
    if debug('cat /etc/NetworkManager/system-connections/f8-pro-test-wifi.nmconnection') != profile.read_text():
        raise RuntimeError('Image Wi-Fi profile mismatch')
    if 'Size: 0' not in debug('stat /etc/machine-id'):
        raise RuntimeError('Image machine-id is not empty')
    if '../libexec/f8-pro/early-init' not in debug('stat /usr/bin/init'):
        raise RuntimeError('Image init link missing')
    exported_binary = EXPORT / 'early-init'
    debug('dump /usr/libexec/f8-pro/early-init ' + str(exported_binary))
    if not exported_binary.is_file() or digest(exported_binary) != digest(BINARY):
        raise RuntimeError('Image diagnostic binary mismatch')
    if 'PARTUUID=614e0000-0000-4b53-8000-1d28000054a9' not in debug('cat /etc/fstab'):
        raise RuntimeError('Unexpected fstab')
    features = run(['dumpe2fs', '-h', str(image)])
    feature_line = next(x for x in features.splitlines() if x.startswith('Filesystem features:'))
    if 'orphan_file' in feature_line or 'metadata_csum_seed' in feature_line:
        raise RuntimeError('Unsupported filesystem features')
    record = {
        'created_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'variant': 'boot-diagnostic', 'size_bytes': SIZE, 'sha256': digest(image),
        'static_diagnostic_sha256': digest(BINARY), 'original_candidate_preserved': True,
        'private_wifi_contents_verified_without_logging': True,
        'uses_existing_dedicated_ssh_public_key': True,
        'filesystem_checked': True, 'hardware_boot_tested': False,
        'screen_rendering_tested_on_tablet': False,
        'flash_start_lba': '0x00078000', 'factory_boot_unchanged': True,
        'diagnostic_root': str(ROOT),
        'limitations': ['No KDE or wizard', 'Framebuffer monitor is diagnostic only',
                        'PID-file presence does not prove service health',
                        'Does not display kernel errors before rootfs init']
    }
    (EXPORT / 'manifest.json').write_text(json.dumps(record, indent=2) + '\n')
    (EXPORT / 'SHA256SUMS').write_text(record['sha256'] + '  ' + image.name + '\n')
    print(json.dumps(record), flush=True)


if __name__ == '__main__':
    main()
