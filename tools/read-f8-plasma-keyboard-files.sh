#!/bin/sh
set -eu
python3 -I - <<'PY'
import json,subprocess
out={}
for n,args in {'files':['dpkg-query','-L','plasma-keyboard'],'ldd':['ldd','/usr/bin/plasma-keyboard'],'help':['sh','-c','QT_QPA_PLATFORM=offscreen plasma-keyboard --help 2>&1 | head -45'],'qml':['sh','-c','find /usr/lib/aarch64-linux-gnu/qt6/qml/QtQuick/VirtualKeyboard -name "*.qml" | head -25']}.items():
 p=subprocess.run(args,capture_output=True,text=True,timeout=12);out[n]={'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr}
print(json.dumps(out,indent=2))
PY
