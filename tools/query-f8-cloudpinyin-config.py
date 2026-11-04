import json,subprocess
code="""import dbus,json
b=dbus.SessionBus();c=dbus.Interface(b.get_object('org.fcitx.Fcitx5','/controller'),'org.fcitx.Fcitx.Controller1');o={'can_restart':bool(c.CanRestart())}
c.Refresh()
for path in ['fcitx://config/addon/cloudpinyin','fcitx://config/inputmethod/pinyin']:
 try:o[path]=str(c.GetConfig(path))[:15000]
 except Exception as e:o[path]=str(e)
print(json.dumps(o))
"""
pre=['runuser','-u','likimk','--','env','XDG_RUNTIME_DIR=/run/user/1602','DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1602/bus'];r=subprocess.run(pre+['python3','-c',code],capture_output=True,text=True,timeout=15);print(json.dumps({'exit':r.returncode,'stdout':r.stdout,'stderr':r.stderr}))
