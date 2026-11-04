#!/bin/bash
# Create an isolated firmware staging copy. No service enablement or disk image.
set -euo pipefail
project=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
state="$project/analysis/rootfs-validation/build-state.json"
manifest="$project/vendor/ubuntu-5.10.160/manifest.json"
archive="$project/vendor/ubuntu-5.10.160/vendor-hardware.tar"
root=$(python3 - "$state" <<'PY'
import json, sys
s = json.load(open(sys.argv[1]))
assert s['qemu_userland_checks_passed'] and not s['flashable']
print(s['rootfs_path'])
PY
)
case "$root" in /var/tmp/f8-pro-*/rootfs-pristine) ;; *) echo 'Unexpected source staging path' >&2; exit 1 ;; esac
target="$(dirname -- "$root")/rootfs-vendor-staging"
[ "$(id -u)" -eq 0 ] || { echo 'Run inside the build environment as root.' >&2; exit 1; }
[ ! -e "$target" ] || { echo 'Staging destination already exists.' >&2; exit 1; }
python3 - "$archive" "$manifest" <<'PY'
import hashlib, json, pathlib, sys
with open(sys.argv[1], 'rb') as stream:
    assert hashlib.file_digest(stream, 'sha256').hexdigest() == json.load(open(sys.argv[2]))['archive']['sha256']
PY
cp --archive --reflink=auto -- "$root" "$target"
# Select data explicitly. Runtime verification showed that Ubuntu loads the
# external bcmdhd_pcie module despite CONFIG_BCMDHD=y; module installation and
# service activation belong to the next integration stage. No Ubuntu ELF libraries used.
bsdtar -xpf "$archive" -C "$target" etc/firmware usr/lib/firmware vendor/etc/firmware etc/iqfiles
python3 - "$target" "$manifest" "$project" <<'PY'
import datetime, hashlib, json, pathlib, sys
root, manifest, project = map(pathlib.Path, sys.argv[1:])
original = json.loads(manifest.read_text())
roots = ('/etc/firmware', '/usr/lib/firmware', '/vendor/etc/firmware', '/etc/iqfiles')
verified = []
for entry in original['rootfs_entries']:
    if not any(entry['path'] == p or entry['path'].startswith(p + '/') for p in roots):
        continue
    path = root / entry['path'].lstrip('/')
    assert path.resolve().is_relative_to(root.resolve()), entry['path']
    if entry['kind'] == 1:
        with path.open('rb') as stream:
            assert hashlib.file_digest(stream, 'sha256').hexdigest() == entry['sha256'], entry['path']
        assert path.stat().st_mode & 0o7777 == int(entry['mode'], 8)
        assert (path.stat().st_uid, path.stat().st_gid) == (entry['uid'], entry['gid'])
    elif entry['kind'] == 7:
        assert path.is_symlink() and str(path.readlink()) == entry['target']
    else:
        assert path.is_dir()
    verified.append(entry['path'])
record = dict(rootfs_path=str(root), created_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
              archive_sha256=original['archive']['sha256'], verified_entries=verified,
              firmware_data_staged=True, vendor_modules_auto_loaded=False,
              ubuntu_userspace_installed=False, services_enabled=False,
              hardware_boot_tested=False, flashable=False,
              source_rootfs_unchanged=True)
output = project / 'analysis/vendor-staging'
output.mkdir(exist_ok=True)
(output / 'build-state.json').write_text(json.dumps(record, indent=2) + '\n')
print('Verified staged data entries:', len(verified))
print('Staging rootfs:', root)
PY
chroot "$target" /usr/bin/true
