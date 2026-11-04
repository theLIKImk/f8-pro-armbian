import base64,json
from pathlib import Path
P=Path(__file__).resolve().parents[1];src=P/'armbian/power'
files={}
for name in ['performance_state.py','performance-panel.py','performance-apply.py','performance-startup.py']:
 files['/usr/local/lib/f8-pro/'+name]=[0o755 if name!='performance_state.py' else 0o644,base64.b64encode((src/name).read_bytes()).decode()]
for name,dest in [('performance-limits.json','/etc/f8-pro/performance-limits.json'),('f8-performance.desktop','/usr/share/applications/f8-performance.desktop'),('org.f8pro.performance.policy','/usr/share/polkit-1/actions/org.f8pro.performance.policy')]:files[dest]=[0o644,base64.b64encode((src/name).read_bytes()).decode()]
for name in ['f8-performance-gpu-start.service','f8-performance-cpu-start.service']:files['/etc/systemd/system/'+name]=[0o644,base64.b64encode((src/name).read_bytes()).decode()]
code='''import base64,json,os,shutil,subprocess,time
from pathlib import Path
assert os.geteuid()==0 and os.environ.get('SUDO_USER')=='likimk'
files=json.loads(base64.b64decode(DATA));backup=Path('/var/lib/f8-pro/performance-panel-backup-'+str(time.time_ns()));backup.mkdir(mode=0o700)
for name,(mode,data) in files.items():
 p=Path(name);assert not p.is_symlink()
 if p.exists():
  b=backup/p.relative_to('/');b.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,b)
 p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(base64.b64decode(data));p.chmod(mode);os.chown(p,0,0)
subprocess.run(['systemctl','daemon-reload'],check=True,capture_output=True,timeout=10)
subprocess.run(['systemctl','add-wants','f8-desktop.target','f8-performance-gpu-start.service','f8-performance-cpu-start.service'],check=True,capture_output=True,timeout=10)
desktop=Path('/home/likimk/Desktop/F8-Performance.desktop')
if desktop.parent.is_dir():
 assert not desktop.is_symlink();shutil.copyfile('/usr/share/applications/f8-performance.desktop',desktop);desktop.chmod(0o755);os.chown(desktop,1602,1602)
u=['runuser','-u','likimk','--','env','XDG_RUNTIME_DIR=/run/user/1602','DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1602/bus','WAYLAND_DISPLAY=wayland-0','QT_QPA_PLATFORM=wayland']
r=subprocess.run(u+['/usr/bin/python3','/usr/local/lib/f8-pro/performance-panel.py','--smoke'],capture_output=True,text=True,timeout=15)
out={'smoke_exit':r.returncode,'smoke':r.stdout,'errors':r.stderr,'backup':str(backup)}
assert r.returncode==0,out
subprocess.run(u+['systemctl','--user','stop','f8-performance-panel.service'],capture_output=True,timeout=10)
r=subprocess.run(u+['systemd-run','--user','--collect','--unit=f8-performance-panel','/usr/bin/python3','/usr/local/lib/f8-pro/performance-panel.py'],capture_output=True,text=True,timeout=10)
out.update(gui_launch_exit=r.returncode,gui_launch_message=r.stderr);print(json.dumps(out,indent=2))
'''.replace('DATA',repr(base64.b64encode(json.dumps(files).encode()).decode()))
(P/'local/hardware/performance-panel-install-runner.py').write_text(code)
