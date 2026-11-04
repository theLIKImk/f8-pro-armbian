import json,os,subprocess
from pathlib import Path
assert os.geteuid()==0 and os.environ.get('SUDO_USER')=='likimk'
out={'input_devices':Path('/proc/bus/input/devices').read_text(),'commands':{}}
for name,args in [('libinput',['libinput','list-devices']),('packages',['dpkg-query','-W','libinput-tools','python3-evdev']),('touch_log',['journalctl','-k','-b','--no-pager','--grep','gsl|touch|input:','-n','70'])]:
 try:r=subprocess.run(args,capture_output=True,text=True,timeout=12);out['commands'][name]={'exit':r.returncode,'stdout':r.stdout,'stderr':r.stderr}
 except (OSError,subprocess.TimeoutExpired) as e:out['commands'][name]={'error':str(e)}
out['input_sysfs']={}
for p in Path('/sys/class/input').glob('event*'):
 d=p/'device';name=(d/'name').read_text().strip()
 if any(k in name.lower() for k in ['touch','gsl','goodix']):out['input_sysfs'][p.name]={'name':name,'properties':(d/'properties').read_text(),'abs':(d/'capabilities/abs').read_text(),'path':str(d.resolve())}
print(json.dumps(out,indent=2))
