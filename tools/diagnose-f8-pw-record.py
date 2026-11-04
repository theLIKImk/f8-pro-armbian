import json,os,subprocess
from pathlib import Path
assert os.geteuid()==0 and os.environ.get('SUDO_USER')=='likimk'
u=['runuser','-u','likimk','--','env','XDG_RUNTIME_DIR=/run/user/1602','DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1602/bus']
out={}
for name,args in [('help',['pw-record','--help']),('status',['wpctl','status']),('source',['wpctl','inspect','@DEFAULT_AUDIO_SOURCE@'])]:
 r=subprocess.run(u+args,capture_output=True,text=True,timeout=12);out[name]={'exit':r.returncode,'stdout':r.stdout,'stderr':r.stderr}
# A single-frame startup probe checks file/container errors, not speech quality.
dest=Path('/home/likimk/.cache/f8-mic-check-20261102/startup-probe.wav')
try:
 r=subprocess.run(u+['pw-record','-v','--rate','48000','--channels','2','--format','s16','--sample-count','1',str(dest)],capture_output=True,text=True,timeout=5)
 out['startup']={'exit':r.returncode,'stderr':r.stderr,'bytes':dest.stat().st_size if dest.exists() else None}
except subprocess.TimeoutExpired:out['startup']={'timeout':True}
if dest.exists():dest.chmod(0o600)
for n in ['pw-record','pw-cat']:
 p=Path(subprocess.check_output(u+['which',n],text=True).strip());out[n]={'path':str(p),'resolved':str(p.resolve()),'size':p.stat().st_size}
 if p.stat().st_size<10000:out[n]['contents']=p.read_text(errors='replace')
out['kernel_tail']=subprocess.run(['journalctl','-k','-b','-n','20','--no-pager'],capture_output=True,text=True).stdout
print(json.dumps(out,indent=2))
