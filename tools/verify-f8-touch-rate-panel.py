import json,os,pwd,subprocess,time
from pathlib import Path
assert os.geteuid()==0 and os.environ.get('SUDO_USER')=='likimk'
helper='/usr/libexec/f8-pro/touch-rate-control.py';meta=json.loads(Path('/usr/libexec/f8-pro/touch-rate-panel/module.json').read_text())
o={}
def call(*args,ok=True):
 r=subprocess.run([helper,*args],capture_output=True,text=True,timeout=30)
 assert (r.returncode==0)==ok,(args,r.stdout,r.stderr)
 return json.loads(r.stdout)
try:
 o['75_apply']=call('apply','75');assert o['75_apply']['state']['period']==252
 assert Path('/sys/module/f8_gsl_shuping/srcversion').read_text().strip()==meta['srcversion']
 assert int(Path('/sys/module/f8_gsl_shuping/parameters/period').read_text())==252
 for n in ['irq_count','read_count']:assert int(Path('/sys/module/f8_gsl_shuping/parameters',n).read_text())>=0
 o['75_keep']=call('keep');assert o['75_keep']['state']['stage']=='kept'
 o['60_apply']=call('apply','60');assert o['60_apply']['state']['period']==316
 assert int(Path('/sys/module/f8_gsl_shuping/parameters/period').read_text())==316
 unit=o['60_apply']['state']['unit']
 r=subprocess.run(['systemctl','show',unit+'.timer','-p','TimersMonotonic'],capture_output=True,text=True,timeout=8);assert r.returncode==0
 o['timer_configuration']=r.stdout
 # Exercise the exact independent rollback service without waiting 45 seconds.
 subprocess.run(['systemctl','start','--wait',unit+'.service'],check=True,timeout=30)
 assert Path('/sys/module/f8_gsl_shuping/srcversion').read_text().strip()==meta['baseline_srcversion']
 state=json.loads(Path('/run/f8-touch-rate-control.json').read_text());assert state['stage']=='original'
 o['independent_rollback_service_verified']=True
 subprocess.run(['systemctl','stop',unit+'.timer'],capture_output=True,timeout=8)
 o['120_apply']=call('apply','120');assert o['120_apply']['state']['period']==122
 o['120_restore']=call('restore');assert o['120_restore']['state']['stage']=='original'
 o['reject59']=call('apply','59',ok=False);o['reject121']=call('apply','121',ok=False)
 r=subprocess.run(['runuser','-u','likimk','--',helper,'restore'],capture_output=True,text=True,timeout=8);assert r.returncode!=0
 o['unprivileged_direct_call_rejected']=True
finally:
 o['final_restore']=call('restore')
 assert Path('/sys/module/f8_gsl_shuping/srcversion').read_text().strip()==meta['baseline_srcversion']
uid=pwd.getpwnam('likimk').pw_uid
u=['runuser','-u','likimk','--','env',f'XDG_RUNTIME_DIR=/run/user/{uid}',f'DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/{uid}/bus']
r=subprocess.run(u+['systemctl','--user','show-environment'],capture_output=True,text=True,timeout=8);assert r.returncode==0
env=[l for l in r.stdout.splitlines() if '=' in l and l.split('=',1)[0] in ['DISPLAY','XAUTHORITY','WAYLAND_DISPLAY']]
r=subprocess.run(u+['systemd-run','--user','--collect','--unit=f8-touch-rate-control-panel',*['--setenv='+l for l in env],'--setenv=QT_QPA_PLATFORM=wayland','/usr/bin/python3','/usr/libexec/f8-pro/touch-rate-panel/panel.py'],capture_output=True,text=True,timeout=10)
o['panel_launch']={'exit':r.returncode,'message':r.stderr};assert r.returncode==0
print(json.dumps(o,indent=2))
