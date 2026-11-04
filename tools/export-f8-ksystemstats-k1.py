import base64,hashlib,json,os,subprocess
from pathlib import Path
assert os.geteuid()==0
root=Path('/usr/lib/aarch64-linux-gnu/qt6/plugins/ksystemstats');out={'plugins':{},'versions':{}}
for kind in ['gpu','disk']:
 name='ksystemstats_plugin_'+kind+'.so';b=(root/name).read_bytes()
 out['plugins'][name]={'base64':base64.b64encode(b).decode(),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
for name in ['ksystemstats','libksysguard-data','libqt6core6t64','libkf6solid6']:
 r=subprocess.run(['dpkg-query','-W','-f=${Version}',name],capture_output=True,text=True);out['versions'][name]=r.stdout
out['diversions']=subprocess.check_output(['dpkg-divert','--list'],text=True)
print(json.dumps(out))
