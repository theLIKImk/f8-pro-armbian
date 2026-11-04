import json,subprocess
from pathlib import Path
P=Path(__file__).resolve().parents[1];dest=P/'local/hardware/armbian-native-desktop-audio-20261101'
out=dest/'reboot-request01.json';runner=dest/'reboot-request01-runner.sh';assert not out.exists() and not runner.exists()
text=(P/'local/hardware/armbian-native-usb-20261101/u5/reboot-request01-runner.sh').read_text().replace('9df01d2b-d624-4364-8d3d-a06ff6847720','3f9b409e-0860-438a-a5eb-2ac768dbafd2').replace('f8-usb-u5-reboot','f8-audio-ucm-reboot')
anchor="subprocess.run(['journalctl','--sync'],check=True,timeout=15)"
assert text.count(anchor)==1
text=text.replace(anchor,"assert Path('/usr/share/alsa/ucm2/F8-PRO/HiFi.conf').exists()\n"+anchor)
runner.write_text(text)
r=subprocess.run(['python3',str(P/'tools/ssh-f8-desktop.py'),'--address','192.168.1.227','--script',str(runner),'--sudo'],capture_output=True,text=True,timeout=100)
assert r.returncode==0,r.stderr[-1600:]
d=json.loads(r.stdout);out.write_text(json.dumps(d,indent=2)+'\n');print(json.dumps(d,indent=2))
