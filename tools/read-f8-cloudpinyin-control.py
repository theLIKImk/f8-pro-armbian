import json,subprocess
from pathlib import Path
pre=['runuser','-u','likimk','--','env','XDG_RUNTIME_DIR=/run/user/1602','DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1602/bus']
o={}
for name,args in {'kwin':pre+['busctl','--user','introspect','org.kde.KWin','/VirtualKeyboard'],'fcitx':pre+['busctl','--user','introspect','org.fcitx.Fcitx5','/controller'],'strings':['sh','-c',"strings /usr/lib/aarch64-linux-gnu/fcitx5/libcloudpinyin.so | grep -E 'Baidu|Google|Engine|https?://' | head -20"]}.items():
 r=subprocess.run(args,capture_output=True,text=True,timeout=10);o[name]={'out':r.stdout[:6500],'err':r.stderr[:500],'exit':r.returncode}
print(json.dumps(o))
