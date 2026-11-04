"""Prepare a backup-first root installer for the user-accepted mic profile."""
import base64
from pathlib import Path
P=Path(__file__).resolve().parents[1]
data=base64.b64encode((P/'armbian/audio/ucm2/HiFi.conf').read_bytes()).decode()
code='''import base64,hashlib,json,os,shutil,subprocess,time,wave
from pathlib import Path
assert os.geteuid()==0 and os.environ.get('SUDO_USER')=='likimk'
u=['runuser','-u','likimk','--','env','XDG_RUNTIME_DIR=/run/user/1602','DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1602/bus']
subprocess.run(u+['systemctl','--user','stop','f8-mic-check-r1.service'],capture_output=True,check=True,timeout=12)
p=Path('/usr/share/alsa/ucm2/F8-PRO/HiFi.conf');assert p.is_file() and not p.is_symlink()
before=p.read_bytes();after=base64.b64decode(DATA)
oldmic=before.split(b'SectionDevice."Mic"',1);newmic=after.split(b'SectionDevice."Mic"',1)
assert len(oldmic)==len(newmic)==2 and oldmic[0]==newmic[0], 'Playback configuration must be byte-identical'
backup=Path('/var/lib/f8-pro/mic-left-20261102');backup.mkdir(mode=0o700,parents=True,exist_ok=True)
if not (backup/'HiFi.conf.before').exists():shutil.copy2(p,backup/'HiFi.conf.before')
state=Path('/var/lib/alsa/asound.state')
if state.exists() and not (backup/'asound.state.before').exists():shutil.copy2(state,backup/'asound.state.before')
controls={'ALC Capture Function':'Left','ALC Capture Max PGA':'5','Left Channel Capture Volume':'8','Right Channel Capture Volume':'0','ADC Data Select':'Left Left'}
def ctl(name):return subprocess.check_output(['amixer','-c','0','cget','name='+name],text=True)
pre={n:ctl(n) for n in controls}
if not (backup/'controls.before.json').exists():(backup/'controls.before.json').write_text(json.dumps(pre,indent=2))
p.write_bytes(after);p.chmod(0o644);os.chown(p,0,0)
for name,value in controls.items():subprocess.run(['amixer','-q','-c','0','cset','name='+name,value],check=True,capture_output=True)
subprocess.run(['alsactl','store','0'],check=True,capture_output=True,timeout=10)
# Recreate the UCM manager, then check the controls during a single-frame
# capture; no speech is needed and no recording is transferred.
subprocess.run(u+['systemctl','--user','restart','wireplumber.service'],check=True,capture_output=True,timeout=15)
time.sleep(3)
probe=Path('/home/likimk/.cache/f8-mic-check-20261102/persistent-probe.wav')
r=subprocess.run(u+['pw-record','--rate','48000','--channels','2','--format','s16','--sample-count','1',str(probe)],capture_output=True,text=True,timeout=10)
probe.chmod(0o600)
with wave.open(str(probe),'rb') as w:frames=w.getnframes();assert frames==1
post={n:ctl(n) for n in controls}
expected={'ALC Capture Function':'2','ALC Capture Max PGA':'5','Left Channel Capture Volume':'8','Right Channel Capture Volume':'0','ADC Data Select':'1'}
for n,v in expected.items():assert next(x.split('values=',1)[1].strip() for x in post[n].splitlines() if ': values=' in x)==v,(n,post[n])
subprocess.run(['alsactl','store','0'],check=True,capture_output=True,timeout=10)
out={'ucm_sha256':hashlib.sha256(after).hexdigest(),'playback_section_unchanged':True,'backup':str(backup),'wireplumber_restarted':True,'fresh_capture_frames':frames,'fresh_capture_exit':r.returncode,'controls_after_fresh_ucm_capture':post,'cold_boot_verified':False,'audio_uploaded':False}
(backup/'result.json').write_text(json.dumps(out,indent=2)+'\\n');print(json.dumps(out,indent=2))
'''.replace('DATA',repr(data))
(P/'local/hardware/mic-left-default-runner.py').write_text(code)
