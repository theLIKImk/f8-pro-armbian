import json,subprocess,pwd,hashlib,os
from pathlib import Path
u=['runuser','-u','likimk','--','env','XDG_RUNTIME_DIR=/run/user/1602','DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1602/bus']
def run(a):
 r=subprocess.run(a,capture_output=True,text=True,timeout=10);return dict(exit=r.returncode,stdout=r.stdout,stderr=r.stderr)
m=json.loads(Path('/usr/share/f8-pro/fcitx5/manifest.json').read_text());checks={}
for name,v in m['files'].items():
 p=Path('/')/name;checks[name]=dict(hash=hashlib.sha256(p.read_bytes()).hexdigest()==v['sha256'],mode=oct(p.stat().st_mode&0o777))
o={'files':checks,'skel_profile':Path('/etc/skel/.config/fcitx5/profile').read_text(),'user_profile':Path('/home/likimk/.config/fcitx5/profile').read_text(),'kwin':run(u+['kreadconfig6','--file','kwinrc','--group','Wayland','--key','InputMethod']),'processes':run(['pgrep','-u','1602','-a','-f','^/usr/bin/fcitx5']),'test_service':run(u+['systemctl','--user','status','f8-fcitx5-input-test.service','--no-pager']),'test_state':None,'current_im':run(u+['fcitx5-remote','-n']),'osk_log':run(u+['journalctl','--user','--since=-7min','--grep=fcitx5|panic|wgpu|Adapter','-n','25','--no-pager']),'links':{n:(Path('/')/n).is_symlink() for n in m['links']}}
p=Path('/home/likimk/.local/state/f8-pro/fcitx5-input-test.json')
if p.is_file():o['test_state']=json.loads(p.read_text())
assert all(v['hash'] for v in checks.values());assert all(o['links'].values())
print(json.dumps(o))
