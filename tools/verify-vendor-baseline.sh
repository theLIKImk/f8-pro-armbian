#!/bin/bash
set -euo pipefail
project=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
base="$project/vendor/ubuntu-5.10.160"
output="$project/analysis/baseline-validation"
mkdir -p "$output"
python3 - "$base" <<'PY'
import hashlib, json, pathlib, sys, tarfile
root = pathlib.Path(sys.argv[1])
manifest = json.loads((root / 'manifest.json').read_text())
for asset in manifest['boot_assets']:
    with (root / asset['file']).open('rb') as stream:
        assert hashlib.file_digest(stream, 'sha256').hexdigest() == asset['sha256'], asset['file']
archive = root / manifest['archive']['file']
with archive.open('rb') as stream:
    assert hashlib.file_digest(stream, 'sha256').hexdigest() == manifest['archive']['sha256']
with tarfile.open(archive) as tar:
    assert len(tar.getmembers()) == len(manifest['rootfs_entries'])
    for entry in manifest['rootfs_entries']:
        member = tar.getmember(entry['path'].lstrip('/'))
        assert member.mode == int(entry['mode'], 8)
        assert (member.uid, member.gid) == (entry['uid'], entry['gid'])
        if entry['kind'] == 1:
            with tar.extractfile(member) as stream:
                assert hashlib.file_digest(stream, 'sha256').hexdigest() == entry['sha256'], entry['path']
        elif entry['kind'] == 7:
            assert member.issym() and member.linkname == entry['target']
        else:
            assert member.isdir()
print('All original boot assets and', len(manifest['rootfs_entries']), 'hardware entries verified')
PY
mkimage -l "$base/boot-assets/boot.img" > "$output/boot-fit.txt"
dtc -I dtb -O dts -o "$output/ubuntu-board.dts" "$base/boot-assets/board.dtb" 2> "$output/dtc-diagnostics.txt"
sh -n "$project/tools/collect-hardware.sh"
bash -n "$project/tools/fetch-arch-rootfs.sh"
bash -n "$project/tools/check-build-host.sh"
bash -n "$project/tools/prepare-arch-rootfs.sh"
printf '%s\n' 'SHA-256, archive metadata, FIT listing, DTB conversion and shell syntax checks passed.'
