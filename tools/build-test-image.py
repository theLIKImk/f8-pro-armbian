"""Seal the candidate and build a checked ext4 partition image, never flash it.

Without private Wi-Fi input, only --unprovisioned is permitted. A successful
filesystem check is not evidence of a successful physical hardware boot.
"""
import argparse
import datetime
import gzip
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import uuid

PROJECT = Path(__file__).resolve().parent.parent
ROOT = Path('/var/tmp/f8-pro-archlinux-20261027/rootfs-vendor-staging')
WORKSPACE = ROOT.parent


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def seal():
    # Never traverse a mounted /proc or /dev while copying the filesystem.
    for row in Path('/proc/self/mountinfo').read_text().splitlines():
        mountpoint = row.split()[4].replace('\\040', ' ')
        if mountpoint == str(ROOT) or mountpoint.startswith(str(ROOT) + '/'):
            raise RuntimeError('Unmount the private chroot checks before building the image')
    if (ROOT / 'etc/machine-id').read_bytes():
        raise RuntimeError('Candidate contains an assigned machine-id')
    if list((ROOT / 'etc/ssh').glob('ssh_host_*_key')):
        raise RuntimeError('Candidate still contains SSH host private keys')
    # A per-build pacman master secret must not be shipped to every device.
    keyring = ROOT / 'etc/pacman.d/gnupg'
    if keyring.exists():
        if keyring.is_symlink() or not keyring.resolve().is_relative_to(ROOT):
            raise RuntimeError('Unexpected package keyring location')
        subprocess.run(['gpgconf', '--homedir', str(keyring), '--kill', 'all'], capture_output=True)
        shutil.rmtree(keyring)
    for name in ('var/lib/f8-pro/keyring-ready', 'var/lib/systemd/random-seed'):
        path = ROOT / name
        if path.is_symlink() or path.is_file():
            path.unlink()
    for name, mode in (('dev', 0o755), ('proc', 0o555), ('sys', 0o555), ('run', 0o755), ('tmp', 0o1777)):
        directory = ROOT / name
        if directory.is_symlink() or not directory.resolve().is_relative_to(ROOT):
            raise RuntimeError('Unexpected runtime directory')
        for path in directory.iterdir():
            if path.is_symlink() or not path.is_dir():
                path.unlink()
            else:
                shutil.rmtree(path)
        directory.chmod(mode)
    cache = ROOT / 'var/cache/pacman/pkg'
    for path in cache.iterdir():
        if path.is_file() or path.is_symlink():
            path.unlink()
    for path in ROOT.rglob('*'):
        if path.name == 'f8-pro-test-ed25519':
            raise RuntimeError('The dedicated client private key was copied into the candidate')


def build(unprovisioned, resume=False):
    if os.getuid() != 0 or not (ROOT / 'etc/arch-release').is_file():
        raise RuntimeError('Run inside the isolated Linux build environment as root')
    state = json.loads((PROJECT / 'analysis/test-rootfs/integration.json').read_text())
    check = json.loads((PROJECT / 'analysis/test-rootfs/verification.json').read_text())
    if not check['ssh_key_only_configuration_passed']:
        raise RuntimeError('Complete offline verification first')
    wifi = (ROOT / 'var/lib/f8-pro/wifi-provisioned').is_file()
    profile = ROOT / 'etc/NetworkManager/system-connections/f8-pro-test-wifi.nmconnection'
    if wifi:
        if not profile.is_file() or profile.stat().st_mode & 0o777 != 0o600:
            raise RuntimeError('Private network profile missing or permissions invalid')
    elif not unprovisioned:
        raise RuntimeError('Fill local/first-boot-network.json and inject it before producing the Wi-Fi test variant')
    variant = 'wifi-test' if wifi else 'pending-wifi'
    artifacts = WORKSPACE / 'artifacts'
    artifacts.mkdir(exist_ok=True)
    image = artifacts / ('f8-pro-arch-' + variant + '.img')
    if image.exists() and not resume:
        raise RuntimeError('Image already exists; archive or explicitly select a new build before rerunning')
    size = 8 * 1024 ** 3
    if not resume:
        seal()
        with image.open('xb') as stream:
            stream.truncate(size)
    if not image.is_file() or image.is_symlink():
        raise RuntimeError('The output must be a regular image file')
    logdir = PROJECT / 'analysis/test-rootfs'
    if not resume:
        result = subprocess.run(['mke2fs', '-F', '-t', 'ext4', '-b', '4096', '-m', '1',
                             '-L', 'F8_ARCH_TEST', '-U', str(uuid.uuid4()),
                             '-O', '^orphan_file,^metadata_csum_seed',
                             '-E', 'lazy_itable_init=0,lazy_journal_init=0,root_owner=0:0',
                                 '-d', str(ROOT), str(image)], capture_output=True, text=True)
        (logdir / 'mke2fs.txt').write_text(result.stdout + result.stderr)
        if result.returncode:
            raise RuntimeError('Image population failed; inspect mke2fs.txt')
    result = subprocess.run(['e2fsck', '-f', '-n', str(image)], capture_output=True, text=True)
    (logdir / 'e2fsck.txt').write_text(result.stdout + result.stderr)
    if result.returncode:
        raise RuntimeError('Filesystem check failed')
    header = subprocess.run(['dumpe2fs', '-h', str(image)], capture_output=True, text=True, check=True)
    (logdir / 'ext4-header.txt').write_text(header.stdout + header.stderr)
    features = next(line for line in header.stdout.splitlines() if line.startswith('Filesystem features:'))
    if 'orphan_file' in features or 'metadata_csum_seed' in features:
        raise RuntimeError('Unexpected newer ext4 feature enabled')
    fs = subprocess.run(['debugfs', '-R', 'cat /etc/fstab', str(image)], capture_output=True, text=True, check=True)
    if 'PARTUUID=614e0000-0000-4b53-8000-1d28000054a9' not in fs.stdout:
        raise RuntimeError('Image fstab does not match the confirmed root partition')
    compressed = image.with_suffix('.img.gz')
    if not resume or not compressed.exists():
        with image.open('rb') as source, compressed.open('xb') as raw:
            with gzip.GzipFile(fileobj=raw, mode='wb', filename='', compresslevel=1, mtime=0) as stream:
                shutil.copyfileobj(source, stream, 4 * 1024 * 1024)
    # Verify every decompressed byte, not only the gzip footer.
    raw_sha = digest(image)
    with gzip.open(compressed, 'rb') as stream:
        if hashlib.file_digest(stream, 'sha256').hexdigest() != raw_sha:
            raise RuntimeError('Compressed image read-back mismatch')
    # DrvFS does not reliably share the current Windows token's restricted ACL.
    # Export privately on Linux; Export-F8-Test.ps1 copies as the Windows owner.
    export = WORKSPACE / 'exports' / variant
    export.mkdir(parents=True, exist_ok=True)
    export.parent.chmod(0o700)
    export.chmod(0o700)
    copied = export / compressed.name
    shutil.copyfile(compressed, copied)
    copied.chmod(0o600)
    compressed_sha = digest(compressed)
    if digest(copied) != compressed_sha:
        raise RuntimeError('Exported image SHA-256 mismatch')
    boot = PROJECT / 'vendor/ubuntu-5.10.160/boot-assets/boot.img'
    shutil.copyfile(boot, export / 'factory-boot.img')
    manifest = dict(created_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                    variant=variant, partition_image_bytes=size, image_sha256=raw_sha,
                    gzip_sha256=compressed_sha, gzip_bytes=copied.stat().st_size,
                    export_directory=str(export), root_start_sector=491520,
                    original_root_partition_bytes=246960619520,
                    original_boot_sha256=digest(boot), filesystem_check_passed=True,
                    gzip_full_readback_passed=True, wifi_credentials_injected=wifi,
                    ssh_user='alarm', ssh_access='dedicated_key_only', temporary_passwordless_sudo=True,
                    package_signing_master_secret_included=False, ssh_host_keys_included=False,
                    desktop_installed=False, account_wizard_installed=False,
                    hardware_boot_tested=False, automatically_flashed=False,
                    ready_for_requested_wifi_test=wifi)
    (logdir / ('image-' + variant + '.json')).write_text(json.dumps(manifest, indent=2) + '\n')
    (export / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    (export / 'SHA256SUMS').write_text(compressed_sha + '  ' + copied.name + '\n' + digest(boot) + '  factory-boot.img\n')
    (export / 'README.txt').write_text(
        'F8-PRO Arch Linux ARM diagnostic partition image\n'
        'This is not a complete Rockchip update.img and must be decompressed before use.\n'
        'No physical hardware boot has been tested. KDE and account wizard are not installed.\n'
        + ('Wi-Fi profile is private and embedded.\n' if wifi else 'Wi-Fi credentials are NOT included. This variant is not ready for the requested Wi-Fi boot test.\n')
        + 'SSH is dedicated-key only. The alarm diagnostic account has temporary passwordless sudo.\n'
        'The factory boot payload is preserved. Do not write loader, GPT, OEM or userdata as part of this artifact.\n')
    print('Created and checked:', copied)
    print('Compressed bytes:', copied.stat().st_size)
    print('Wi-Fi profile present:', wifi)
    print('Physical hardware boot tested: False')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--unprovisioned', action='store_true', help='Build only a clearly labeled Wi-Fi-pending base artifact')
    parser.add_argument('--resume-export', action='store_true', help='Recheck an existing image and complete export after an interrupted export')
    args = parser.parse_args()
    build(args.unprovisioned, args.resume_export)
