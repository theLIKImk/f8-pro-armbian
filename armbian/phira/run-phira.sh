#!/bin/sh
set -eu
appdir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
cd "$appdir"
export ALSA_CONFIG_PATH="$appdir/alsa-pulse.conf"
exec "$appdir/phira" "$@"
