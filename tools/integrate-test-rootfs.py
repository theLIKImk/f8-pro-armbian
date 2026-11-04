"""Install verified board assets and key-only test access into the WSL candidate.

Run as root inside the Linux build environment after update-test-rootfs.sh.
Never starts target hardware services or loads target kernel modules on the host.
"""
import datetime
import hashlib
import json
import os
import re
from pathlib import Path
import shutil
import subprocess
import tarfile

PROJECT = Path(__file__).resolve().parent.parent
ROOT = Path('/var/tmp/f8-pro-archlinux-20261027/rootfs-vendor-staging')
WORKSPACE = ROOT.parent


def destination(name):
    path = ROOT / name.lstrip('/')
    if not path.parent.resolve().is_relative_to(ROOT.resolve()):
        raise ValueError('Destination escapes candidate: ' + name)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def write(name, content, mode=0o644):
    path = destination(name)
    if path.is_symlink():
        path.unlink()
    path.write_bytes(content if isinstance(content, bytes) else content.encode())
    path.chmod(mode)
    return path


def target(*arguments, check=True):
    return subprocess.run(['chroot', str(ROOT), *arguments], check=check,
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)


def integrate():
    if os.getuid() != 0 or not (ROOT / 'etc/arch-release').is_file():
        raise RuntimeError('Expected root access to the isolated Arch build tree')
    if not (PROJECT / 'analysis/test-rootfs/packages.txt').is_file():
        raise RuntimeError('Complete the package update first')
    if not shutil.which('ssh-keygen'):
        raise RuntimeError('The native build host needs openssh-client for ssh-keygen')
    output = PROJECT / 'analysis/test-rootfs'
    output.mkdir(exist_ok=True)
    original = json.loads((PROJECT / 'vendor/ubuntu-5.10.160/manifest.json').read_text())
    archive = PROJECT / 'vendor/ubuntu-5.10.160/vendor-hardware.tar'
    with archive.open('rb') as stream:
        if hashlib.file_digest(stream, 'sha256').hexdigest() != original['archive']['sha256']:
            raise RuntimeError('Vendor archive SHA-256 changed')
    selected = {
        '/vendor/etc/firmware/fw_bcm43752a2_pcie_ag.bin': '/vendor/etc/firmware/fw_bcm43752a2_pcie_ag.bin',
        '/vendor/etc/firmware/nvram_AP6275P.txt': '/vendor/etc/firmware/nvram_AP6275P.txt',
        '/vendor/etc/firmware/clm_bcm43752a2_pcie_ag.blob': '/vendor/etc/firmware/clm_bcm43752a2_pcie_ag.blob',
        '/vendor/etc/firmware/config.txt': '/vendor/etc/firmware/config.txt',
        '/vendor/etc/firmware/BCM4362A2.hcd': '/vendor/etc/firmware/BCM4362A2.hcd',
        '/usr/lib/firmware/mali_csffw.bin': '/usr/lib/firmware/mali_csffw.bin',
        '/vendor/lib/modules/bcmdhd_pcie.ko': '/usr/lib/modules/5.10.160/updates/bcmdhd_pcie.ko',
    }
    installed = []
    with tarfile.open(archive) as tar:
        for source, name in selected.items():
            metadata = next(e for e in original['rootfs_entries'] if e['path'] == source)
            payload = tar.extractfile(source.lstrip('/')).read()
            digest = hashlib.sha256(payload).hexdigest()
            if digest != metadata['sha256']:
                raise RuntimeError('Vendor payload hash mismatch: ' + source)
            path = write(name, payload, 0o644)
            if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
                raise RuntimeError('Installed payload hash mismatch')
            installed.append({'source': source, 'path': name, 'sha256': digest})
    metadata = json.loads((PROJECT / 'analysis/vendor-userspace/manifest.json').read_text())
    helper = PROJECT / 'analysis/vendor-userspace/brcm_patchram_plus1'
    digest = hashlib.sha256(helper.read_bytes()).hexdigest()
    if digest != next(m['sha256'] for m in metadata if m['file'] == helper.name):
        raise RuntimeError('Bluetooth helper SHA-256 changed')
    write('/usr/libexec/f8-pro/brcm_patchram_plus1', helper.read_bytes(), 0o755)
    installed.append({'path': '/usr/libexec/f8-pro/brcm_patchram_plus1', 'sha256': digest})
    overlay = PROJECT / 'rootfs-overlay'
    for path in sorted(overlay.rglob('*')):
        if not path.is_file() or '__pycache__' in path.parts or path.suffix == '.pyc':
            continue
        name = '/' + path.relative_to(overlay).as_posix()
        mode = 0o755 if '/usr/libexec/' in name else 0o644
        if '/sudoers.d/' in name:
            mode = 0o440
        write(name, path.read_bytes(), mode)
        installed.append({'path': name, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
    # Remove a redundant main-file policy block from early verification runs;
    # the normal upstream Include already reads our numbered drop-in.
    ssh_config = destination('/etc/ssh/sshd_config')
    original_config = re.sub(r'(?s)^# BEGIN F8 TEST POLICY\n.*?# END F8 TEST POLICY\n', '', ssh_config.read_text())
    if original_config != ssh_config.read_text():
        write('/etc/ssh/sshd_config', original_config)
    cache = ROOT / 'usr/libexec/f8-pro/__pycache__'
    if cache.is_dir():
        for path in cache.glob('*.pyc'):
            path.unlink()
        if not any(cache.iterdir()):
            cache.rmdir()
    write('/usr/lib/modules/5.10.160/modules.order', 'updates/bcmdhd_pcie.ko\n')
    depmod = subprocess.run(['depmod', '-b', str(ROOT), '-a', '5.10.160'], capture_output=True, text=True)
    (output / 'depmod.txt').write_text(depmod.stdout + depmod.stderr)
    if depmod.returncode:
        raise RuntimeError('depmod failed; inspect depmod.txt')
    dry_run = target('/usr/bin/modprobe', '--show-depends', '--set-version', '5.10.160', 'bcmdhd_pcie')
    (output / 'module-dry-run.txt').write_text(dry_run.stdout)
    if 'bcmdhd_pcie.ko' not in dry_run.stdout:
        raise RuntimeError('The module lookup did not select bcmdhd_pcie')

    keys = WORKSPACE / 'private-keys'
    keys.mkdir(mode=0o700, exist_ok=True)
    keys.chmod(0o700)
    key = keys / 'f8-pro-test-ed25519'
    if not key.exists() and not key.with_suffix('.pub').exists():
        subprocess.run(['ssh-keygen', '-q', '-t', 'ed25519', '-N', '', '-C', 'f8-pro-diagnostic', '-f', str(key)], check=True)
    if not key.is_file() or not key.with_suffix('.pub').is_file():
        raise RuntimeError('Incomplete dedicated key pair')
    key.chmod(0o600)
    public = key.with_suffix('.pub').read_text().strip()
    if not public.startswith('ssh-ed25519 '):
        raise RuntimeError('Unexpected SSH key type')
    (output / 'test-access.pub').write_text(public + '\n')
    alarm = next(line.split(':') for line in (ROOT / 'etc/passwd').read_text().splitlines() if line.startswith('alarm:'))
    uid, gid = int(alarm[2]), int(alarm[3])
    directory = destination('/home/alarm/.ssh/authorized_keys').parent
    directory.chmod(0o700)
    os.chown(directory, uid, gid)
    authorized = write('/home/alarm/.ssh/authorized_keys', public + '\n', 0o600)
    os.chown(authorized, uid, gid)
    for user in ('root', 'alarm'):
        target('/usr/bin/passwd', '-l', user)
    target('/usr/bin/usermod', '-a', '-G', 'wheel,audio,video', 'alarm')
    target('/usr/sbin/visudo', '-c', '-f', '/etc/sudoers')
    # Host identities must be generated independently on each physical install.
    write('/etc/machine-id', '')
    dbus_id = destination('/var/lib/dbus/machine-id')
    if dbus_id.is_symlink() or dbus_id.exists():
        dbus_id.unlink()
    dbus_id.symlink_to('../../../etc/machine-id')
    for path in (ROOT / 'etc/ssh').glob('ssh_host_*_key*'):
        if path.is_file() or path.is_symlink():
            path.unlink()
    resolver = destination('/etc/resolv.conf')
    if resolver.is_symlink() or resolver.exists():
        resolver.unlink()
    resolver.symlink_to('../run/systemd/resolve/stub-resolv.conf')
    subprocess.run(['systemctl', '--root', str(ROOT), 'disable', 'systemd-networkd.service',
                    'systemd-networkd-wait-online.service', 'dhcpcd.service'], check=True, capture_output=True, text=True)
    subprocess.run(['systemctl', '--root', str(ROOT), 'enable', 'NetworkManager.service',
                    'systemd-resolved.service', 'sshd.service', 'f8-pro-wifi.service',
                    'f8-pro-bluetooth.service', 'bluetooth.service', 'f8-pro-keyring.service'], check=True, capture_output=True, text=True)
    # Check library resolution without executing the firmware initializer.
    loader = target('/usr/lib/ld-linux-aarch64.so.1', '--list', '/usr/libexec/f8-pro/brcm_patchram_plus1')
    (output / 'bluetooth-loader.txt').write_text(loader.stdout)
    record = dict(rootfs_path=str(ROOT), integrated_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                  kernel_release='5.10.160', installed_files=installed,
                  private_key_path=str(key), ssh_user='alarm', ssh_authentication='dedicated_ed25519_key_only',
                  temporary_passwordless_sudo=True, wifi_credentials_injected=False,
                  target_services_started_on_build_host=False, hardware_boot_tested=False,
                  desktop_installed=False, first_boot_wizard_installed=False,
                  flashable_release_ready=False)
    (output / 'integration.json').write_text(json.dumps(record, indent=2) + '\n')
    print('Integrated and verified board files:', len(installed))
    print('SSH access uses a dedicated key; private key stays outside the rootfs.')


if __name__ == '__main__':
    integrate()
