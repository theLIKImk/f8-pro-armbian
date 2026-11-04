#!/bin/bash
# Download and verify the official generic aarch64 rootfs. Does not extract it.
set -euo pipefail
project=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
destination="$project/downloads"
mkdir -p "$destination"
cd "$destination"
archive=ArchLinuxARM-aarch64-latest.tar.gz
fingerprint=68B3537F39A313B3E574D06777193F152BDBE6A6
base=${1:-https://os.archlinuxarm.org/os}
for tool in curl gpg python3; do command -v "$tool" >/dev/null; done
fetch() {
    curl --fail --location --proto '=https' --proto-redir '=https' \
        --retry 3 --connect-timeout 20 --max-time 1800 \
        --output "$2.part" "$1"
    mv -- "$2.part" "$2"
}
if [ ! -f "$archive" ]; then fetch "$base/$archive" "$archive"; fi
fetch "$base/$archive.sig" "$archive.sig"
fetch "https://keyserver.ubuntu.com/pks/lookup?op=get&search=0x$fingerprint" archlinuxarm-build-key.asc
keyring=$(mktemp -d /tmp/f8-pro-gpg.XXXXXXXX)
# Only public signing material is used; keep all GPG state in this temporary directory.
trap 'rm -rf -- "$keyring"' EXIT
gpg --batch --no-options --homedir "$keyring" --with-colons --show-keys archlinuxarm-build-key.asc > signing-key.txt
grep -q "^fpr:::::::::$fingerprint:" signing-key.txt
gpg --batch --no-options --homedir "$keyring" --import archlinuxarm-build-key.asc
gpg --batch --no-options --homedir "$keyring" --status-fd 1 \
    --verify "$archive.sig" "$archive" > signature-status.txt 2> signature-details.txt
python3 - "$archive" "$fingerprint" "$base/$archive" <<'PY'
import datetime, hashlib, json, pathlib, sys
archive, fingerprint, url = sys.argv[1:]
status = pathlib.Path('signature-status.txt').read_text()
signers = [line.split()[2:] for line in status.splitlines() if line.startswith('[GNUPG:] VALIDSIG ')]
assert any(fingerprint in (fields[0], fields[-1]) for fields in signers), 'Unexpected signer'
path = pathlib.Path(archive)
with path.open('rb') as stream:
    sha256 = hashlib.file_digest(stream, 'sha256').hexdigest()
record = dict(url=url, file=archive, size=path.stat().st_size, sha256=sha256,
              signing_key_fingerprint=fingerprint, signature_verified=True,
              verified_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
              official_key_source='https://archlinuxarm.org/about/package-signing')
pathlib.Path('rootfs-source.json').write_text(json.dumps(record, indent=2) + '\n')
print(json.dumps(record, indent=2))
PY
