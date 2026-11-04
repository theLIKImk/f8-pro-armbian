#!/bin/bash
# Prepare a pristine Linux-filesystem rootfs and test ARM userland via QEMU.
# No services are started and no image or physical disk is written.
set -euo pipefail
project=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
workspace=${1:-/var/tmp/f8-pro-archlinux-20261027}
case "$workspace" in /var/tmp/f8-pro-*) ;; *) echo 'Use a dedicated /var/tmp/f8-pro-* directory.' >&2; exit 1 ;; esac
[ "$(id -u)" -eq 0 ] || { echo 'Root is needed to preserve Linux ownership.' >&2; exit 1; }
for tool in bsdtar python3 chroot; do command -v "$tool" >/dev/null; done
archive="$project/downloads/ArchLinuxARM-aarch64-latest.tar.gz"
python3 - "$project/downloads/rootfs-source.json" "$archive" <<'PY'
import hashlib, json, pathlib, sys
record = json.loads(pathlib.Path(sys.argv[1]).read_text())
assert record['signature_verified'] is True
assert record['signing_key_fingerprint'] == '68B3537F39A313B3E574D06777193F152BDBE6A6'
with pathlib.Path(sys.argv[2]).open('rb') as stream:
    assert hashlib.file_digest(stream, 'sha256').hexdigest() == record['sha256']
PY
root="$workspace/rootfs-pristine"
if [ -e "$root" ]; then
    echo "Rootfs already exists: $root; choose a new dedicated build workspace." >&2
    exit 1
fi
mkdir -p -- "$workspace"
filesystem=$(stat -f -c %T "$workspace")
case "$filesystem" in ext2/ext3|ext4|btrfs|xfs) ;; *) echo "Unsupported staging filesystem: $filesystem" >&2; exit 1 ;; esac
mkdir -m 0755 -- "$root"
bsdtar --numeric-owner -xpf "$archive" -C "$root"
output="$project/analysis/rootfs-validation"
mkdir -p "$output"
chroot "$root" /usr/bin/true
chroot "$root" /usr/bin/bash --noprofile --norc -c 'printf "ARM bash OK\n"; getconf GNU_LIBC_VERSION' > "$output/userland.txt" 2>&1
chroot "$root" /usr/bin/pacman --version > "$output/pacman-version.txt" 2>&1
chroot "$root" /usr/lib/systemd/systemd --version > "$output/systemd-version.txt" 2>&1
chroot "$root" /usr/bin/pacman -Q > "$output/packages.txt" 2>&1
python3 - "$project" "$root" "$filesystem" <<'PY'
import datetime, json, pathlib, sys
project, root, filesystem = sys.argv[1:]
record = dict(rootfs_path=root, filesystem=filesystem,
              created_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
              source=json.loads((pathlib.Path(project) / 'downloads/rootfs-source.json').read_text()),
              qemu_userland_checks_passed=True, hardware_boot_tested=False,
              vendor_integrated=False, flashable=False,
              note='Pristine upstream rootfs, default upstream accounts; no network or services started. Not a release image.')
(pathlib.Path(project) / 'analysis/rootfs-validation/build-state.json').write_text(json.dumps(record, indent=2) + '\n')
print(json.dumps(record, indent=2))
PY
