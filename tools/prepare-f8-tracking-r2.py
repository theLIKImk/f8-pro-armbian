import base64
from pathlib import Path
P=Path(__file__).resolve().parents[1]
capture=base64.b64encode((P/'armbian/touch/capture-tracking.py').read_bytes()).decode()
install=base64.b64encode((P/'local/hardware/multitouch-install-runner.py').read_bytes()).decode()
code='''import base64,json,os,subprocess,time
from pathlib import Path
assert os.geteuid()==0 and os.environ.get('SUDO_USER')=='likimk'
folder=Path('/var/lib/f8-pro/touch-diagnostic');folder.mkdir(parents=True,exist_ok=True);assert not folder.is_symlink();folder.chmod(0o700)
assert not (folder/'r2/frames.jsonl').exists(),'Preserve prior R2 evidence before another run'
script=folder/'capture-tracking-r2.py';script.write_bytes(base64.b64decode(CAPTURE));script.chmod(0o700)
run=Path('/run/f8-touch-diagnostic');run.mkdir(exist_ok=True);assert not run.is_symlink();run.chmod(0o755)
flag=run/'start';assert not flag.is_symlink();flag.write_text('0');os.chown(flag,1602,1602);flag.chmod(0o600)
r=subprocess.run(['systemd-run','--collect','--unit=f8-touch-capture-r2','--property=RuntimeMaxSec=380','/usr/bin/python3',str(script)],capture_output=True,text=True,timeout=8)
assert r.returncode==0,r.stderr
time.sleep(1)
summary=json.loads((folder/'r2/summary.json').read_text());assert summary['phase']=='waiting_for_user_button',summary
print(json.dumps({'capture_ready':summary,'unit':r.stderr}))
exec(compile(base64.b64decode(INSTALL),'install-multitouch','exec'))
'''.replace('CAPTURE',repr(capture)).replace('INSTALL',repr(install))
(P/'local/hardware/multitouch-r2-runner.py').write_text(code,encoding='utf-8')
