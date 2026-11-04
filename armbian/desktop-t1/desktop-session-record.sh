#!/bin/sh
umask 077
mkdir -p "$XDG_RUNTIME_DIR/f8-desktop"
python3 -I - <<'PY'
import json,os,time
from pathlib import Path
p=Path(os.environ['XDG_RUNTIME_DIR'])/'f8-desktop/session.json'
p.write_text(json.dumps({'uid':os.getuid(),'session_type':os.environ.get('XDG_SESSION_TYPE'),
 'wayland_display':os.environ.get('WAYLAND_DISPLAY'),'desktop':os.environ.get('XDG_CURRENT_DESKTOP'),
 'uptime':time.monotonic()},indent=2)+'\n')
PY
sleep 3
busctl --user --timeout=5 call org.kde.KWin /KWin org.kde.KWin supportInformation >"$XDG_RUNTIME_DIR/f8-desktop/kwin-info.txt" 2>&1 || true
