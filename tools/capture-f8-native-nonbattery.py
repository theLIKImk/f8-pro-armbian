import base64,json,subprocess
from pathlib import Path
P=Path(__file__).resolve().parents[1]
public=P/'local/hardware/armbian-native-desktop-t1r1-failure-20261030-01/SSHKEY.PUB'
subprocess.run(['python3',str(P/'tools/register-f8-desktop-hostkey.py'),'--key-base64',base64.b64encode(public.read_bytes()).decode()],check=True)
dest=P/'local/hardware/armbian-native-desktop-t1r2-success-20261030-01';dest.mkdir(exist_ok=True)
out=dest/'nonbattery-baseline.json';assert not out.exists()
r=subprocess.run(['python3',str(P/'tools/ssh-f8-desktop.py'),'--address','192.168.1.227','--script',str(P/'tools/read-f8-native-nonbattery.sh'),'--sudo'],capture_output=True,text=True,timeout=100)
assert r.returncode==0,r.stderr[-1500:]
data=json.loads(r.stdout);out.write_text(json.dumps(data,indent=2)+'\n')
print(json.dumps({k:data[k] for k in ['boot_id','kernel','root_mount','services','failed','audio_cards','alsa_devices','backlight','bluetooth_nodes','rfkill','audio_bt_kernel']},indent=2))
print('KWin Mali-G610 hardware renderer:', 'Mali-G610' in data['kwin'].get('stdout',''))
