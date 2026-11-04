#!/bin/sh
# Ubuntu 20.04-compatible collection launcher; no network connection required.
set -eu
umask 077
case "${1:-}" in
    --help) printf 'Run as the desktop user: sh run-collect.sh [existing-output-parent]\n'; exit 0 ;;
esac
if [ "$(id -u)" -eq 0 ]; then
    echo 'Please run this launcher as the logged-in desktop user, without sudo.' >&2
    exit 1
fi
here=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
parent=${1:-$HOME}
[ -d "$parent" ] || { echo 'Output parent must be an existing directory.' >&2; exit 1; }
parent=$(CDPATH= cd -- "$parent" && pwd)
result=$(mktemp -d "$parent/f8-hardware-$(date +%Y%m%d-%H%M%S)-XXXXXX")
printf 'Collecting desktop diagnostics into %s\n' "$result"
sh "$here/collect-hardware.sh" "$result/desktop" all
if command -v sudo >/dev/null 2>&1; then
    printf '\nAdministrator password may be requested for kernel logs; input stays on this tablet.\n'
    if sudo -v; then
        if sudo sh "$here/collect-hardware.sh" "$result/system" system; then
            sudo chown -R "$(id -u):$(id -g)" "$result/system"
        else
            printf 'Administrator collection failed; desktop results are retained.\n' >"$result/admin-collection.txt"
            if [ -d "$result/system" ]; then sudo chown -R "$(id -u):$(id -g)" "$result/system" || true; fi
        fi
    else
        printf 'Administrator collection was skipped; desktop results are retained.\n' >"$result/admin-collection.txt"
    fi
else
    printf 'sudo unavailable; desktop results are retained.\n' >"$result/admin-collection.txt"
fi
printf 'Hardware has not been automatically marked as working. Inspect check-status.tsv and the actual logs.\n' >"$result/README.txt"
archive="$result.tar.gz"
tar -czf "$archive" -C "$parent" "$(basename -- "$result")"
printf '\nDone. Copy this file back to the project:\n%s\n' "$archive"
