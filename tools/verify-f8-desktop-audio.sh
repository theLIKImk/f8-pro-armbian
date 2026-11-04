#!/bin/sh
set -eu
python3 -I - <<'PY'
import hashlib,json,subprocess
from pathlib import Path
prefix=['runuser','-u','f8test','--','env','XDG_RUNTIME_DIR=/run/user/1601','DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1601/bus']
def cmd(args):
    p=subprocess.run(args,capture_output=True,text=True,timeout=12)
    assert p.returncode==0,p.stderr
    return p.stdout
def user(args):return cmd(prefix+args)
hashes={'/usr/share/alsa/ucm2/conf.d/rockchip_es8388/rockchip,es8388-codec.conf':'e75e5fb1d5d798c5da77759685e63095ad9ca5c44be9164d843ec6747276e5cf','/usr/share/alsa/ucm2/F8-PRO/HiFi.conf':'bbe36bf455e06359f89475dd85001a0786c807714472a438e227e661a47100f2'}
for name,digest in hashes.items():assert hashlib.sha256(Path(name).read_bytes()).hexdigest()==digest
cards=json.loads(user(['pactl','--format=json','list','cards']));card=next(c for c in cards if c['name']=='alsa_card.platform-es8388-sound')
assert card['active_profile']=='HiFi',card['active_profile']
name=user(['pactl','get-default-sink']).strip();assert name=='alsa_output.platform-es8388-sound.HiFi__Speaker__sink',name
sink=next(s for s in json.loads(user(['pactl','--format=json','list','sinks'])) if s['name']==name)
assert sink['properties'].get('api.alsa.open.ucm')=='true'
assert sink['active_port']=='[Out] Speaker'
mixer={n:cmd(['amixer','-c','0','sget',n]) for n in ['Speaker','OUT2','Output 2','PCM']}
assert 'Playback [on]' in mixer['Speaker'] and 'Playback [on]' in mixer['OUT2'],mixer
assert 'Playback 24' in mixer['Output 2']
services={n:cmd(['systemctl','is-active',n]).strip() for n in ['sddm','f8-live-ssh','f8-usb-otg']}
failed=cmd(['systemctl','--failed','--no-legend','--no-pager']);assert not failed.strip()
print(json.dumps({'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'default_sink':name,'card_profile':card['active_profile'],'active_port':sink['active_port'],'ucm_opened':True,'mute':sink['mute'],'volume':sink['volume'],'sink_state':sink['state'],'mixer':mixer,'files_sha256':hashes,'services':services,'failed_units':failed},indent=2))
PY
