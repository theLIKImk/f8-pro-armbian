import json,subprocess
from pathlib import Path
P=Path(__file__).resolve().parents[1]
dest=P/'local/hardware/armbian-native-audio-a2-20261030-01';dest.mkdir(exist_ok=True)
collected={}
for name,script in [('backlight.json','read-f8-backlight-ownership.sh'),('desktop.json','verify-f8-native-desktop.sh'),('audio.json','read-f8-audio-runtime.sh')]:
    out=dest/name;assert not out.exists(),'Preserve existing evidence'
    r=subprocess.run(['python3',str(P/'tools/ssh-f8-desktop.py'),'--address','192.168.1.227','--script',str(P/'tools'/script),'--sudo'],capture_output=True,text=True,timeout=100)
    assert r.returncode==0,r.stderr[-1300:]
    data=json.loads(r.stdout);out.write_text(json.dumps(data,indent=2)+'\n');collected[name]=data
    if name=='backlight.json':print(json.dumps(data,indent=2),flush=True)
    elif name=='desktop.json':print(json.dumps({'boot_id':data['boot_id'],'reboot_persistence_confirmed':data['reboot_persistence_confirmed'],'keyboard':data['keyboard']},indent=2),flush=True)
    else:print(json.dumps({'cards':data['cards'],'devices':data['devices'],'pipewire':data['pipewire'],'sound_log':data['sound_log']},indent=2),flush=True)
lines='\n'.join(s for group in collected['backlight.json']['pinmux'].values() for s in group)
assert 'pin 138 (gpio4-10): febf0020.pwm' in lines and 'group pwm14m1-pins' in lines
assert 'pin 114 (gpio3-18): febf0020.pwm' not in lines
mfile=P/'outputs/armbian/official-f8-native-audio-a2/preflight.json';m=json.loads(mfile.read_text())
backup=mfile.with_name('preflight-before-hardware-verification.json')
if not backup.exists():backup.write_bytes(mfile.read_bytes())
m.update({'cold_boot_verified':True,'motor_stopped_user_confirmed':True,'screen_brightness_adjustment_user_confirmed':True,
          'runtime_pwm_pin_verified':True,'verified_boot_id':collected['desktop.json']['boot_id'],
          'reboot_persistence_confirmed':collected['desktop.json']['reboot_persistence_confirmed'],
          'audio_playback_verified':False,'battery_work_deferred_by_user':True})
mfile.write_text(json.dumps(m,indent=2)+'\n')
(dest/'user-feedback.json').write_text(json.dumps({'brightness_changes_screen':True,'brightness_adjustment_no_motor_vibration':True,'audio_playback_not_tested_this_round':True,'battery_work_deferred':True},indent=2)+'\n')
print('A2 backlight/motor fix verified; audio output remains pending',flush=True)
