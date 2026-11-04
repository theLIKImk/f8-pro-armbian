#!/bin/sh
set -eu
python3 - <<'PY'
import importlib.util,json,subprocess
from pathlib import Path
modules={}
for n in ['PySide6','PyQt6','tkinter','dbus','gi']:
    try:modules[n]=importlib.util.find_spec(n) is not None
    except ImportError:modules[n]=False
print(json.dumps({'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'modules':modules}))
PY
command -v qml6 || true
command -v qml || true
command -v g++ || true
dpkg-query -W qt6-base-dev python3-pyside6.qtwidgets python3-pyqt6 python3-tk 2>/dev/null || true
