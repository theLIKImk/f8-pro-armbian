#!/bin/sh
set -eu
project=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
for script in collect-hardware.sh run-collect.sh prepare-ubuntu-tools.sh; do
    dash -n "$project/tools/$script"
done
bash -n "$project/tools/stage-vendor-rootfs.sh"
python3 "$project/tools/test-collection-launcher.py"
python3 "$project/tools/package-ubuntu-kit.py"
