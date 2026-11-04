import base64
from pathlib import Path
P=Path(__file__).resolve().parents[1];data=base64.b64encode((P/'armbian/kde/ksystemstats/sensor-probe.py').read_bytes()).decode()
code='''import base64,json,os,subprocess
from pathlib import Path
assert os.geteuid()==0 and os.environ.get('SUDO_USER')=='likimk'
p=Path('/var/tmp/f8-pro-ksystemstats-k1/sensor-probe.py');p.write_bytes(base64.b64decode(DATA));p.chmod(0o644)
# Root-only build directory: copy just the public test script for the user.
dest=Path('/usr/local/lib/f8-pro/kde-sensor-probe.py');dest.write_bytes(p.read_bytes());dest.chmod(0o755)
u=['runuser','-u','likimk','--','env','XDG_RUNTIME_DIR=/run/user/1602','DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1602/bus','WAYLAND_DISPLAY=wayland-0']
r=subprocess.run(u+['/usr/bin/python3',str(dest)],capture_output=True,text=True,timeout=20)
print(json.dumps({'exit':r.returncode,'stdout':r.stdout,'stderr':r.stderr},indent=2))
'''.replace('DATA',repr(data));(P/'local/hardware/kde-sensor-probe-runner.py').write_text(code)
