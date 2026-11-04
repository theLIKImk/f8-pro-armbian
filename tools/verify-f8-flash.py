import hashlib,json,os,pwd,subprocess
from pathlib import Path
assert os.geteuid()==0 and os.environ.get('SUDO_USER')=='likimk'
def run(a):
 r=subprocess.run(a,capture_output=True,text=True,timeout=12);return {'exit':r.returncode,'stdout':r.stdout,'stderr':r.stderr}
led=Path('/sys/class/leds/f8:white:flash');helper='/usr/libexec/f8-pro/flash-control.py'
o={'off_helper':run([helper,'off'])};assert o['off_helper']['exit']==0
assert (led/'brightness').read_text().strip()=='0'
o['unload']=run(['rmmod','f8_flash']);assert o['unload']['exit']==0
o['reload']=run(['modprobe','f8-flash']);assert o['reload']['exit']==0
assert (led/'brightness').read_text().strip()=='0'
o['module_sha256']=hashlib.sha256(Path('/usr/lib/modules',os.uname().release,'extra/f8-pro/f8-flash.ko').read_bytes()).hexdigest()
o['polkit']=run(['pkaction','--action-id','org.f8pro.flash.control','--verbose']);assert o['polkit']['exit']==0
o['unprivileged_helper']=run(['runuser','-u','likimk','--',helper,'off']);assert o['unprivileged_helper']['exit']!=0
uid=pwd.getpwnam('likimk').pw_uid
u=['runuser','-u','likimk','--','env',f'XDG_RUNTIME_DIR=/run/user/{uid}',f'DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/{uid}/bus']
o['panel']=run(u+['systemctl','--user','show','f8-flash-panel','-p','ActiveState','-p','MainPID','-p','Result'])
o['gpio113']=[l for l in Path('/sys/kernel/debug/gpio').read_text().splitlines() if 'gpio-113 ' in l]
o['brightness']=(led/'brightness').read_text().strip()
o['autoload']=Path('/etc/modules-load.d/f8-flash.conf').read_text()
o['cold_boot_verified']=False
print(json.dumps(o,indent=2))
