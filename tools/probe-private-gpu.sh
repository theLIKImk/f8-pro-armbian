#!/bin/sh
# Offscreen 16x16 probe as alarm; does not change display mode or system links.
set -eu
prefix=/opt/f8-pro/vendor-gpu-g13p0-20261028
[ -r "$prefix/lib/libEGL.so.1" ] || exit 2
umask 077
out=$(mktemp -d /tmp/f8-gpu-probe-XXXXXXXX)
if timeout 40 env LD_LIBRARY_PATH="$prefix/lib" python3 "$prefix/probe-gpu-context.py" egl \
    --egl-platform gbm --drm-device /dev/dri/card0 \
    --egl-library "$prefix/lib/libEGL.so.1" --gles-library "$prefix/lib/libGLESv2.so.2" \
    --gbm-library "$prefix/lib/libgbm.so.1" --output "$out/egl.json" >"$out/native.txt" 2>&1; then
    result=0
else
    result=$?
fi
if [ -f "$out/egl.json" ]; then cat "$out/egl.json"; else head -c 2000 "$out/native.txt"; fi
printf '\nEXIT_CODE=%s\nREPORT=%s\n' "$result" "$out"
exit "$result"
