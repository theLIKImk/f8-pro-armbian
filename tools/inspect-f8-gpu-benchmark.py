import json,os,subprocess,shutil
from pathlib import Path
assert os.geteuid()==0 and os.environ.get('SUDO_USER')=='likimk'
out={'commands':{x:shutil.which(x) for x in ['glmark2-es2-wayland','glmark2-wayland','glmark2-es2','kmscube','eglinfo','vkcube','glxinfo']}}
for name in ['ALC Capture Function','ALC Capture Max PGA','Left Channel Capture Volume','Right Channel Capture Volume','ADC Data Select']:
 out[name]=subprocess.check_output(['amixer','-c','0','cget','name='+name],text=True)
out['polkit_mode']=oct(Path('/usr/lib/polkit-1/polkit-agent-helper-1').stat().st_mode&0o7777)
out['ssh_enabled']=Path('/etc/systemd/system/f8-desktop.target.wants/ssh.service').is_symlink()
cmd=out['commands'].get('glmark2-es2-wayland') or out['commands'].get('glmark2-wayland')
if cmd:
 r=subprocess.run([cmd,'--help'],capture_output=True,text=True,timeout=8);out['benchmark_help']=r.stdout+r.stderr
print(json.dumps(out,indent=2))
