"""Install card-specific UCM and reload desktop audio, restoring on failure."""
import base64,json,subprocess
from pathlib import Path
P=Path(__file__).resolve().parents[1];dest=P/'local/hardware/armbian-native-desktop-audio-20261101'
out=dest/'ucm-install01.json';runner=dest/'ucm-install01-runner.sh';assert not out.exists() and not runner.exists()
files={'/usr/share/alsa/ucm2/conf.d/rockchip_es8388/rockchip,es8388-codec.conf':P/'armbian/audio/ucm2/rockchip,es8388-codec.conf','/usr/share/alsa/ucm2/F8-PRO/HiFi.conf':P/'armbian/audio/ucm2/HiFi.conf'}
payload={name:base64.b64encode(path.read_bytes()).decode() for name,path in files.items()}
code='''import base64,hashlib,json,subprocess,time
from pathlib import Path
assert Path('/proc/sys/kernel/random/boot_id').read_text().strip()=='3f9b409e-0860-438a-a5eb-2ac768dbafd2'
assert Path('/proc/asound/card0/id').read_text().strip()=='rockchipes8388c'
claims='\\n'.join(p.read_text() for p in Path('/sys/kernel/debug/pinctrl').glob('*/pinmux-pins'))
assert 'pin 138 (gpio4-10): febf0020.pwm' in claims and 'group pwm14m1-pins' in claims
payload=PAYLOAD
for name in payload:assert not Path(name).exists() and not Path(name).is_symlink(),name
stage=Path('/var/lib/f8-pro/audio-ucm01');stage.mkdir(exist_ok=False)
prefix=['runuser','-u','f8test','--','env','XDG_RUNTIME_DIR=/run/user/1601','DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1601/bus']
def cmd(args,check=True):
    r=subprocess.run(args,capture_output=True,text=True,timeout=15)
    d={'exit':r.returncode,'stdout':r.stdout,'stderr':r.stderr}
    if check and r.returncode:raise RuntimeError(str(d))
    return d
def user(args,check=True):return cmd(prefix+args,check)
result={'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'before_sinks':user(['pactl','--format=json','list','sinks']),'before_cards':user(['pactl','--format=json','list','cards'])}
cmd(['alsactl','-f',str(stage/'before.state'),'store','0'])
created=[]
try:
    result['initial_quiet_volume']=user(['pactl','set-sink-volume','@DEFAULT_SINK@','25%'])
    for name,encoded in payload.items():
        path=Path(name);path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(base64.b64decode(encoded));path.chmod(0o644);created.append(path)
    result['ucm_parse']=cmd(['alsaucm','-c','hw:0','list','_verbs'])
    assert 'HiFi' in result['ucm_parse']['stdout']
    result['wireplumber_restart']=user(['systemctl','--user','restart','wireplumber.service'])
    deadline=time.monotonic()+12
    while True:
        cards=json.loads(user(['pactl','--format=json','list','cards'])['stdout'])
        card=next((c for c in cards if c['name']=='alsa_card.platform-es8388-sound'),None)
        if card and 'HiFi' in card.get('profiles',{}):break
        if time.monotonic()>deadline:raise RuntimeError('UCM HiFi profile not exposed: '+str(cards))
        time.sleep(.4)
    if card['active_profile']!='HiFi':result['select_hifi']=user(['pactl','set-card-profile',card['name'],'HiFi'])
    deadline=time.monotonic()+8
    while True:
        sinks=json.loads(user(['pactl','--format=json','list','sinks'])['stdout'])
        sink=next((s for s in sinks if s['properties'].get('alsa.card_name')=='rockchip,es8388-codec' or 'es8388-sound' in s['name']),None)
        if sink:break
        if time.monotonic()>deadline:raise RuntimeError('No onboard speaker sink')
        time.sleep(.3)
    result['set_default']=user(['pactl','set-default-sink',sink['name']])
    result['quiet_volume']=user(['pactl','set-sink-volume',sink['name'],'25%'])
    result['unmute']=user(['pactl','set-sink-mute',sink['name'],'0'])
    result['after_cards']=user(['pactl','--format=json','list','cards'])
    result['after_sinks']=user(['pactl','--format=json','list','sinks'])
    result['after_mixer']=cmd(['amixer','-c','0','scontents'])
    result['files_sha256']={name:hashlib.sha256(Path(name).read_bytes()).hexdigest() for name in payload}
    result['success']=True
except Exception as error:
    result['error']=str(error)
    for path in created:path.unlink()
    result['rollback_restart']=user(['systemctl','--user','restart','wireplumber.service'],False)
    result['rollback_mixer']=cmd(['alsactl','-f',str(stage/'before.state'),'restore','0'],False)
    result['success']=False
(stage/'result.json').write_text(json.dumps(result,indent=2)+'\\n')
print(json.dumps(result,indent=2))
'''.replace('PAYLOAD',repr(payload))
runner.write_text("#!/bin/sh\nset -eu\npython3 -I - <<'PY'\n"+code+'\nPY\n')
r=subprocess.run(['python3',str(P/'tools/ssh-f8-desktop.py'),'--address','192.168.1.227','--script',str(runner),'--sudo'],capture_output=True,text=True,timeout=100)
assert r.returncode==0,r.stderr[-1500:]
d=json.loads(r.stdout);out.write_text(json.dumps(d,indent=2)+'\n');print(json.dumps({k:d.get(k) for k in ['success','error','ucm_parse','files_sha256','after_cards','after_sinks']},indent=2))
