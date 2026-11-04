import base64,json,subprocess
from pathlib import Path
P=Path(__file__).resolve().parents[1]
payload=base64.b64encode((P/'armbian/first-run/first-run.py').read_bytes()).decode()
script=P/'local/hardware/first-run-preview-runner.sh'
script.write_text("#!/bin/sh\nset -eu\npython3 -I - <<'PY'\n"+f'''import base64,subprocess,os,json
from pathlib import Path
p=Path.home()/'.cache/f8-first-run-preview-r1';p.mkdir(exist_ok=True)
(p/'first-run.py').write_bytes(base64.b64decode({payload!r}))
env=dict(os.environ,QT_QPA_PLATFORM='offscreen',XDG_RUNTIME_DIR='/run/user/1601',DBUS_SESSION_BUS_ADDRESS='unix:path=/run/user/1601/bus')
r=subprocess.run(['python3',str(p/'first-run.py'),'--preview','--render-preview',str(p/'pages')],env=env,capture_output=True,text=True,timeout=30)
print(json.dumps(dict(exit=r.returncode,stdout=r.stdout,stderr=r.stderr,pages=[x.name for x in (p/'pages').glob('*.png')]),indent=2))
assert r.returncode==0
'''+'\nPY\n')
r=subprocess.run(['python3',str(P/'tools/ssh-f8-desktop.py'),'--address','192.168.1.227','--script',str(script)],capture_output=True,text=True)
(P/'local/hardware/first-run-preview01.json').write_text(r.stdout);print(r.stdout);assert r.returncode==0,r.stderr
dest=P/'local/hardware/first-run-preview-r1';dest.mkdir(exist_ok=True)
ssh=['ssh','-T','-i','/var/tmp/f8-pro-archlinux-20261027/private-keys/f8-pro-test-ed25519','-o','BatchMode=yes','-o','IdentitiesOnly=yes','-o','StrictHostKeyChecking=yes','-o','HostKeyAlias=f8-desktop-t1','-o','UserKnownHostsFile=/var/tmp/f8-pro-armbian/desktop-t1-known-hosts','f8test@192.168.1.227']
for n in range(6):
 with (dest/f'page-{n}.png').open('wb') as f:
  subprocess.run(ssh+[f'cat /home/f8test/.cache/f8-first-run-preview-r1/pages/page-{n}.png'],stdout=f,check=True)
