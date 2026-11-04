import ast,base64,hashlib,json,xml.etree.ElementTree as ET
from pathlib import Path
P=Path(__file__).resolve().parents[1];S=P/'armbian/touch';O=P/'outputs/armbian/f8-touch-rate-panel-r1'
m=json.loads((O/'module-check.json').read_text());binary=(O/'f8_gsl_rate.ko').read_bytes()
previous=json.loads((O/'installation-manifest.json').read_text()) if (O/'installation-manifest.json').exists() else {}
assert m['all_import_crcs_verified_against_actual_image'] and hashlib.sha256(binary).hexdigest()==m['sha256']
meta={**m,'baseline_sha256':'bb8fd9db0bf16972e6760ca9d8ba8489e91a516c31269fc770346fe75d7a505d','baseline_srcversion':'6A8F0920D4E483066E520A4'}
files={
 '/usr/libexec/f8-pro/touch-rate-control.py':((S/'rate-control.py').read_bytes(),0o755),
 '/usr/libexec/f8-pro/touch-rate-panel/panel.py':((S/'rate-panel.py').read_bytes(),0o755),
 '/usr/libexec/f8-pro/touch-rate-panel/rate-map.json':((S/'rate-map.json').read_bytes(),0o644),
 '/usr/libexec/f8-pro/touch-rate-panel/module.json':((json.dumps(meta,indent=2)+'\n').encode(),0o644),
 '/usr/libexec/f8-pro/touch-rate-panel/f8_gsl_rate.ko':(binary,0o644),
 '/usr/share/polkit-1/actions/org.f8pro.touchrate.policy':((S/'org.f8pro.touchrate.policy').read_bytes(),0o644),
 '/usr/share/applications/f8-touch-rate.desktop':((S/'f8-touch-rate.desktop').read_bytes(),0o644)}
payload={}
for name,(data,mode) in files.items():
 if name.endswith('.py'):ast.parse(data)
 if name.endswith('.policy'):ET.fromstring(data)
 dest=P/'armbian/rootfs-overlay'/name.lstrip('/');dest.parent.mkdir(parents=True,exist_ok=True)
 if dest.exists():assert hashlib.sha256(dest.read_bytes()).hexdigest() in [hashlib.sha256(data).hexdigest(),previous.get(name,{}).get('sha256')],'Conflicting overlay '+name
 dest.write_bytes(data)
 payload[name]={'data':base64.b64encode(data).decode(),'mode':mode,'sha256':hashlib.sha256(data).hexdigest(),'previous_sha256':previous.get(name,{}).get('sha256')}
code='''import base64,hashlib,json,os,subprocess,time
from pathlib import Path
assert os.geteuid()==0 and os.environ.get('SUDO_USER')=='likimk'
assert os.uname().release=='6.1.115-vendor-rk35xx'
assert Path('/proc/device-tree/model').read_bytes().startswith(b'F8-PRO')
old=Path('/usr/libexec/f8-pro/f8_gsl_shuping.ko')
assert hashlib.sha256(old.read_bytes()).hexdigest()=='bb8fd9db0bf16972e6760ca9d8ba8489e91a516c31269fc770346fe75d7a505d'
base=subprocess.check_output(['modinfo','-F','srcversion',str(old)],text=True).strip()
known=[base,'B769C22C37A1C4330D85F05','1AFFBA60D1DAFFDEAD7BE9F','E302094212AAC7FF0D33572','B33EF6DCB84D7738CE23C07']
v=Path('/sys/module/f8_gsl_shuping/srcversion');assert v.read_text().strip() in known
for label in ['p122-manual1','p128-manual1']:
 unit='f8-touch-rate-rollback-'+label
 subprocess.run(['systemctl','stop',unit+'.timer'],capture_output=True,timeout=8)
 for _ in range(40):
  r=subprocess.run(['systemctl','show',unit+'.service','-p','ActiveState','--value'],capture_output=True,text=True,timeout=5)
  if r.stdout.strip() not in ['active','activating']:break
  time.sleep(.5)
 else:raise RuntimeError('An earlier rollback is still running')
assert not [l for l in Path('/sys/kernel/tracing/kprobe_events').read_text().splitlines() if 'f8_gsl_shuping:' in l]
if v.read_text().strip()!=base:
 subprocess.run(['rmmod','f8_gsl_shuping'],check=True,timeout=12)
 subprocess.run(['insmod',str(old)],check=True,timeout=15);time.sleep(1)
assert v.read_text().strip()==base
files=FILES
for name,data in files.items():
 p=Path(name);assert not p.is_symlink()
 if p.exists():assert hashlib.sha256(p.read_bytes()).hexdigest() in [data['sha256'],data['previous_sha256']],'Conflicting file '+name
for name,data in files.items():
 p=Path(name);p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(base64.b64decode(data['data']));p.chmod(data['mode']);os.chown(p,0,0)
r=subprocess.run(['/usr/libexec/f8-pro/touch-rate-control.py','restore'],capture_output=True,text=True,timeout=15);assert r.returncode==0,r.stderr+r.stdout
policy=subprocess.run(['pkaction','--action-id','org.f8pro.touchrate.control','--verbose'],capture_output=True,text=True,timeout=10);assert policy.returncode==0,policy.stderr
print(json.dumps({'installed':{n:d['sha256'] for n,d in files.items()},'policy':policy.stdout,'initial_state':json.loads(r.stdout),'boot_module_changed':False,'test_app_started':False},indent=2))
'''.replace('FILES',repr(payload))
compile(code,'panel-install','exec');(P/'local/hardware/touch-rate-panel-install-runner.py').write_text(code)
(O/'installation-manifest.json').write_text(json.dumps({n:{k:v[k] for k in ['sha256','mode']} for n,v in payload.items()},indent=2)+'\n')
print('Panel install payload prepared')
