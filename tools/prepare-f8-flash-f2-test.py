import base64,hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parents[1];out=P/'outputs/armbian/f8-flash-f2'
report=json.loads((out/'module-check.json').read_text());data=(out/'f8-flash.ko').read_bytes()
assert report['all_import_crcs_verified'] and hashlib.sha256(data).hexdigest()==report['module_sha256']
code='''import base64,hashlib,json,os,pwd,re,subprocess,time
from pathlib import Path
assert os.geteuid()==0 and os.environ.get('SUDO_USER')=='likimk'
assert os.uname().release=='6.1.115-vendor-rk35xx'
assert Path('/proc/device-tree/model').read_bytes().startswith(b'F8-PRO')
installed=Path('/usr/lib/modules',os.uname().release,'extra/f8-pro/f8-flash.ko')
assert hashlib.sha256(installed.read_bytes()).hexdigest()=='32cc2bc830372bea259164cce21e0e747bbd5fa6f81501817f6654a7cfa618c8'
uid=pwd.getpwnam('likimk').pw_uid
u=['runuser','-u','likimk','--','env',f'XDG_RUNTIME_DIR=/run/user/{uid}',f'DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/{uid}/bus']
subprocess.run(u+['systemctl','--user','stop','f8-flash-panel'],capture_output=True,timeout=10)
subprocess.run(['/usr/libexec/f8-pro/flash-control.py','off'],check=True,capture_output=True,timeout=8)
data=base64.b64decode(MODULE_DATA);assert hashlib.sha256(data).hexdigest()==MODULE_SHA
module=Path('/usr/local/lib/f8-pro/experimental/f8-flash-f2.ko')
assert not module.is_symlink();module.write_bytes(data);module.chmod(0o644)
baseline=float(Path('/proc/uptime').read_text().split()[0]);o={'tests':{}}
subprocess.run(['rmmod','f8_flash'],check=True,timeout=10)
root=Path('/sys/devices/platform/f8-flash');control=root/'control'
def state():
 d=dict(v.split('=',1) for v in (root/'state').read_text().split())
 return {k:(v if k=='mode' else int(v)) for k,v in d.items()}
def write(value):control.write_text(value+'\\n')
try:
 subprocess.run(['insmod',str(module)],check=True,timeout=10)
 assert state()['mode']=='off'
 write('pulse 25');time.sleep(.2);a=state();assert a['mode']=='pulse' and a['output']==25 and a['pwm_edges']>20,a
 time.sleep(.6);assert state()['mode']=='off';o['tests']['pulse_25']=a
 write('steady 25');time.sleep(.3);a=state();time.sleep(.3);b=state()
 assert b['pwm_edges']-a['pwm_edges']>100 and b['output']==25,(a,b)
 o['tests']['pwm_25']={'first':a,'second':b}
 write('steady 75');time.sleep(.3);a=state();assert a['output']==75 and a['level']==75,a
 o['tests']['pwm_75']=a
 write('steady 100');time.sleep(.15);a=state();time.sleep(.15);b=state()
 assert a['output']==100 and a['pwm_edges']==b['pwm_edges'],(a,b)
 o['tests']['steady_100']=b
 write('blink 25 200 300');start=time.monotonic();samples=[]
 for _ in range(20):
  samples.append({'elapsed':round(time.monotonic()-start,3),**state()});time.sleep(.08)
 assert {s['output'] for s in samples}=={0,25},samples
 assert sum(a['output']!=b['output'] for a,b in zip(samples,samples[1:]))>=4,samples
 o['tests']['blink_200_300']=samples
 write('off');a=state();time.sleep(.15);b=state();assert a['pwm_edges']==b['pwm_edges'] and b['output']==0
 for invalid in ['steady 101','blink 25 0 500']:
  try:write(invalid)
  except OSError:pass
  else:raise AssertionError('Accepted invalid setting '+invalid)
 assert state()['mode']=='off';o['tests']['invalid_bounds_rejected']=True
 write('steady 10');time.sleep(5.4);a=state();assert a['mode']=='off' and a['output']==0,a
 o['tests']['watchdog_without_heartbeat']=a
 write('steady 10');time.sleep(3);write('keepalive');time.sleep(3);a=state()
 assert a['mode']=='steady' and a['output']==10,a
 o['tests']['heartbeat_beyond_five_seconds']=a;write('off')
 write('steady 10');time.sleep(.1);subprocess.run(['rmmod','f8_flash'],check=True,timeout=10)
 subprocess.run(['insmod',str(module)],check=True,timeout=10)
 assert state()['mode']=='off';o['tests']['unload_active_pwm_reload_off']=True
 o['final_state']=state();o['module_sha256']=MODULE_SHA
 logs=subprocess.check_output(['dmesg'],text=True)
 recent=[l for l in logs.splitlines() if (m:=re.match(r'\\[\\s*(\\d+\\.\\d+)\\]',l)) and float(m.group(1))>=baseline]
 bad=[l for l in recent if any(t in l for t in ['Oops:','BUG:','WARNING:','sleeping function','Kernel panic'])]
 assert not bad,bad
 o['kernel_new_faults']=bad;o['kernel_flash_messages']=[l for l in recent if 'f8-flash' in l]
 print(json.dumps(o,indent=2))
except BaseException:
 try:write('off')
 except OSError:pass
 subprocess.run(['rmmod','f8_flash'],capture_output=True,timeout=10)
 subprocess.run(['insmod',str(installed)],check=True,timeout=10)
 raise
finally:
 if control.exists():write('off')
'''.replace('MODULE_DATA',repr(base64.b64encode(data).decode())).replace('MODULE_SHA',repr(report['module_sha256']))
compile(code,'f2-test','exec');(P/'local/hardware/flash-f2-test-runner.py').write_text(code)
print('F2 test payload ready')
