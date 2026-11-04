import json
from pathlib import Path
P=Path(__file__).resolve().parents[1]
e=P/'local/hardware/armbian-native-audio-a1-20261030-01'
audio=json.loads((e/'audio-runtime.json').read_text());desktop=json.loads((e/'desktop-acceptance.json').read_text())
quiet=json.loads((e/'quiet-gpio-01.json').read_text())
assert audio['boot_id']==desktop['boot_id'] and desktop['reboot_persistence_confirmed']
assert audio['devices']['7-0011']['driver'].endswith('/ES8323') and 'es8388' in audio['cards']
assert quiet['speaker_off']['exit']==0 and quiet['out2_off']['exit']==0
mfile=P/'outputs/armbian/official-f8-native-audio-a1/preflight.json'
m=json.loads(mfile.read_text());backup=mfile.with_name('preflight-before-hardware-verification.json')
if not backup.exists():backup.write_bytes(mfile.read_bytes())
m.update({'cold_boot_verified':True,'alsa_card_registered':True,'codec_driver':'ES8323','pipewire_sink_created':True,
 'audio_playback_verified':False,'speaker_heard_user_confirmed':False,'unexpected_motor_vibration_user_reported':True,
 'known_backlight_pwm_mux_bug':True,'verified_boot_id':audio['boot_id'],'reboot_persistence_confirmed':True,
 'battery_work_deferred_by_user':True})
mfile.write_text(json.dumps(m,indent=2)+'\n')
feedback={'speaker_sound_heard':False,'vibration':'Whole-device motor-like vibration, user confirmed',
 'virtual_keyboard_user_confirmed_working':True,'speaker_and_out2_temporarily_disabled':True,
 'current_state':'User entered Loader; A2 BOOT candidate ready, not flashed',
 'battery_work_deferred':True}
out=e/'user-feedback.json';assert not out.exists();out.write_text(json.dumps(feedback,indent=2)+'\n')
print('A1 registration and persistence recorded; physical audio remains unverified, PWM defect recorded')
