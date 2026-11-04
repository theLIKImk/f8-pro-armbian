"""Check stripped custom modules and create an independent ABI-labelled archive."""
import hashlib
import json
from pathlib import Path
import struct
import subprocess

P = Path(__file__).resolve().parents[1]
B = Path('/var/tmp/f8-pro-armbian')
BUILD = B / 'kernel-config-build'
ROOT = B / 'custom-modules-install'
RELEASE = '6.1.172-f8-pro-armbian-eval'
directory = ROOT / 'lib/modules' / RELEASE
assert directory.resolve().is_relative_to(ROOT.resolve())
image = json.loads((P / 'analysis/armbian/kernel-build/verified-evaluation-image.json').read_text())
assert image['release'] == RELEASE
for filename in ['build', 'source']:
    path = directory / filename
    if path.is_symlink():
        path.unlink()
modules = sorted(directory.rglob('*.ko'))
assert len(modules) > 100
records = []
for path in modules:
    with path.open('rb') as stream:
        header = stream.read(64)
        stream.seek(0)
        digest = hashlib.file_digest(stream, 'sha256').hexdigest()
    assert header[:6] == b'\x7fELF\x02\x01' and struct.unpack_from('<H', header, 18)[0] == 183, path
    vermagic = subprocess.check_output(['modinfo', '-F', 'vermagic', str(path)], text=True).strip()
    assert vermagic.split()[0] == RELEASE, (path, vermagic)
    records.append({'path': str(path.relative_to(directory)), 'bytes': path.stat().st_size,
                    'sha256': digest, 'vermagic': vermagic})
symvers = BUILD / 'Module.symvers'
symbols = {}
for line in symvers.read_text().splitlines():
    fields = line.split()
    symbols[fields[1]] = int(fields[0], 16)
key_checks = []
for name in ['cw2015_battery', 'bq25890_charger', 'panthor']:
    matches = [path for path in modules if path.stem == name]
    assert len(matches) == 1, (name, matches)
    versions = subprocess.check_output(['modprobe', '--show-modversions', str(matches[0])], text=True)
    checked = 0
    for line in versions.splitlines():
        crc, symbol = line.split()
        assert symbols[symbol] == int(crc, 16), (name, symbol)
        checked += 1
    assert checked > 0
    dependencies = subprocess.check_output(['modprobe', '-d', str(ROOT), '-S', RELEASE,
                                             '--show-depends', name], text=True)
    assert name + '.ko' in dependencies
    key_checks.append({'name': name, 'versioned_symbols_matched': checked,
                       'dependency_resolution': dependencies.splitlines()})
result = subprocess.run(['depmod', '-e', '-E', str(symvers), '-b', str(ROOT), RELEASE],
                        capture_output=True, text=True, check=True)
assert not result.stdout.strip() and not result.stderr.strip(), result.stdout + result.stderr
out = P / 'outputs/armbian/evaluation-kernel'
archive = out / ('modules-' + RELEASE + '.tar.gz')
subprocess.run(['tar', '--sort=name', '--owner=0', '--group=0', '--numeric-owner',
                '-czf', str(archive), '-C', str(ROOT), 'lib/modules/' + RELEASE], check=True)
listing = subprocess.check_output(['tar', '-tzf', str(archive)], text=True).splitlines()
assert all(name.startswith('lib/modules/' + RELEASE + '/') for name in listing)
assert not any(name.endswith('/build') or name.endswith('/source') for name in listing)
with archive.open('rb') as stream:
    digest = hashlib.file_digest(stream, 'sha256').hexdigest()
report = {'scope': 'Offline custom-module architecture, vermagic, CRC and dependency checks; no module loaded',
          'release': RELEASE, 'module_count': len(modules),
          'installed_module_bytes': sum(item['bytes'] for item in records),
          'depmod_symbol_version_check_passed': True, 'key_module_checks': key_checks,
          'archive': str(archive), 'archive_bytes': archive.stat().st_size, 'archive_sha256': digest}
reports = P / 'analysis/armbian/kernel-build'
(reports / 'custom-modules-manifest.json').write_text(json.dumps(records, indent=2) + '\n')
(reports / 'verified-custom-modules.json').write_text(json.dumps(report, indent=2) + '\n')
(out / (archive.name + '.sha256')).write_text(digest + '  ' + archive.name + '\n')
print(json.dumps(report, indent=2))
