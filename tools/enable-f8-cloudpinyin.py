import json,subprocess
code="""import dbus,json,urllib.request
from pathlib import Path
b=dbus.SessionBus();c=dbus.Interface(b.get_object('org.fcitx.Fcitx5','/controller'),'org.fcitx.Fcitx.Controller1')
for path,changes in [('fcitx://config/addon/cloudpinyin',{'Backend':'Baidu','MinimumPinyinLength':'4'}),('fcitx://config/inputmethod/pinyin',{'CloudPinyinEnabled':'True','CloudPinyinIndex':'2','CloudPinyinAnimation':'True'})]:
 raw,_=c.GetConfig(path)
 for k,v in changes.items():raw[k]=dbus.String(v,variant_level=1)
 c.SetConfig(path,raw)
c.Save();c.ReloadAddonConfig('pinyin');c.ReloadAddonConfig('cloudpinyin')
o={}
for path,keys in [('fcitx://config/addon/cloudpinyin',['Backend','MinimumPinyinLength']),('fcitx://config/inputmethod/pinyin',['CloudPinyinEnabled','CloudPinyinIndex'])]:
 raw,_=c.GetConfig(path);o[path]={k:str(raw[k]) for k in keys}
try:
 r=urllib.request.urlopen('https://olimenew.baidu.com/py?input=nihao&inputtype=py&resultcoding=utf-8',timeout=8);data=r.read();o['network_test']={'status':r.status,'json_valid':True,'candidate_nihao_present':'你好' in data.decode('utf-8')};json.loads(data)
except Exception as e:o['network_test']={'error':str(e)}
o['files']={str(p):p.read_text() for p in [Path.home()/'.config/fcitx5/conf/cloudpinyin.conf',Path.home()/'.config/fcitx5/conf/pinyin.conf'] if p.exists()}
print(json.dumps(o))
"""
pre=['runuser','-u','likimk','--','env','XDG_RUNTIME_DIR=/run/user/1602','DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1602/bus'];r=subprocess.run(pre+['python3','-c',code],capture_output=True,text=True,timeout=20);print(json.dumps({'exit':r.returncode,'stdout':r.stdout,'stderr':r.stderr}))
