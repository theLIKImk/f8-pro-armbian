"""Hash-check archived board firmware into a candidate overlay, without enabling it."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

P = Path(__file__).resolve().parents[1]
B = Path('/var/tmp/f8-pro-armbian')
state = json.loads((P / 'analysis/test-rootfs/integration.json').read_text())
source_root = Path(state['rootfs_path'])
assert str(source_root) == '/var/tmp/f8-pro-archlinux-20261027/rootfs-vendor-staging'
target = B / 'wireless-assets'
records = {item['path']: item for item in state['installed_files']}
names = ['fw_bcm43752a2_pcie_ag.bin', 'nvram_AP6275P.txt',
         'clm_bcm43752a2_pcie_ag.blob', 'config.txt', 'BCM4362A2.hcd']
copied = []
for name in names:
    relative = '/vendor/etc/firmware/' + name
    source = source_root / relative.lstrip('/')
    content = source.read_bytes()
    digest = hashlib.sha256(content).hexdigest()
    assert digest == records[relative]['sha256'], name
    directory = 'vendor/etc/firmware' if name.endswith('.hcd') else 'usr/lib/firmware/ap6275p'
    destination = target / directory / name
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(content)
    destination.chmod(0o644)
    copied.append({'path': str(destination.relative_to(target)), 'bytes': len(content), 'sha256': digest})
# Retain the vendor names and offer the target driver's default/lowercase names.
firmware = target / 'usr/lib/firmware/ap6275p'
aliases = {'fw_bcmdhd.bin': 'fw_bcm43752a2_pcie_ag.bin', 'nvram.txt': 'nvram_AP6275P.txt',
           'nvram_ap6275p.txt': 'nvram_AP6275P.txt', 'clm_bcmdhd.blob': 'clm_bcm43752a2_pcie_ag.blob'}
for alias, original in aliases.items():
    path = firmware / alias
    if path.is_symlink():
        assert path.readlink() == Path(original)
    else:
        assert not path.exists(), path
        path.symlink_to(original)
helper_relative = '/usr/libexec/f8-pro/brcm_patchram_plus1'
helper_source = source_root / helper_relative.lstrip('/')
digest = hashlib.sha256(helper_source.read_bytes()).hexdigest()
assert digest == records[helper_relative]['sha256']
helper_target = target / helper_relative.lstrip('/')
helper_target.parent.mkdir(parents=True, exist_ok=True)
shutil.copy2(helper_source, helper_target)
elf = subprocess.check_output(['readelf', '-h', '-l', '-d', str(helper_target)], text=True)
assert 'AArch64' in elf and '/lib/ld-linux-aarch64.so.1' in elf
report = {'scope': 'Archived firmware hashes and candidate paths only; not installed/loaded or validated with target driver',
          'files': copied, 'relative_symlinks': aliases, 'helper_sha256': digest,
          'helper_architecture': 'AArch64', 'helper_interpreter': '/lib/ld-linux-aarch64.so.1',
          'staging_directory': str(target), 'no_old_kernel_modules_copied': True}
out = P / 'analysis/armbian/wireless'
out.mkdir(parents=True, exist_ok=True)
(out / 'verified-assets.json').write_text(json.dumps(report, indent=2) + '\n')
(out / 'helper-elf.txt').write_text(elf)
print(json.dumps(report, indent=2))
