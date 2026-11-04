import base64
from pathlib import Path
P=Path(__file__).resolve().parents[1]
data=base64.b64encode((P/'armbian/audio/mic-check.py').read_bytes()).decode()
code='''import base64,json,os,subprocess
from pathlib import Path
assert os.geteuid()==0 and os.environ.get('SUDO_USER')=='likimk'
p=Path('/usr/local/lib/f8-pro/mic-check.py');p.write_bytes(base64.b64decode(DATA));p.chmod(0o755)
u=['runuser','-u','likimk','--','env','XDG_RUNTIME_DIR=/run/user/1602','DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1602/bus']
subprocess.run(u+['systemctl','--user','stop','f8-mic-check-r1.service'],capture_output=True,timeout=12)
r=subprocess.run(u+['systemd-run','--user','--collect','--unit=f8-mic-check-r1','--setenv=QT_QPA_PLATFORM=wayland','--setenv=WAYLAND_DISPLAY=wayland-0','/usr/bin/python3',str(p)],capture_output=True,text=True,timeout=12)
out={'gui_exit':r.returncode,'gui_stdout':r.stdout,'gui_stderr':r.stderr,'regulators':[]}
for p in Path('/sys/class/regulator').glob('regulator.*'):
 name=(p/'name').read_text().strip() if (p/'name').exists() else ''
 if any(x in name for x in ['cpu','gpu']):
  item={'name':name}
  for prop in ['microvolts','min_microvolts','max_microvolts','state']:
   try:item[prop]=(p/prop).read_text().strip()
   except OSError:pass
  out['regulators'].append(item)
clk=Path('/sys/kernel/debug/clk/clk_summary').read_text();out['cpu_clocks']=[x for x in clk.splitlines() if 'scmi_clk_cpu' in x]
print(json.dumps(out,indent=2))
'''.replace('DATA',repr(data))
(P/'local/hardware/mic-check-install-runner.py').write_text(code)
