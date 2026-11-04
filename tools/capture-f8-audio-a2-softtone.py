import json,subprocess
from pathlib import Path
P=Path(__file__).resolve().parents[1]
dest=P/'local/hardware/armbian-native-audio-a2-20261030-01'
out=dest/'softtone-01.json';runner=dest/'softtone-01-runner.sh'
assert not out.exists() and not runner.exists()
text=(P/'tools/test-f8-audio-a1-softtone.sh').read_text().replace('f8-audio-a1-softtone-02','f8-audio-a2-softtone-01')
anchor="assert Path('/run/user/1601').stat().st_uid==1601\n"
guard="""claims='\\n'.join(p.read_text() for p in Path('/sys/kernel/debug/pinctrl').glob('*/pinmux-pins'))
assert 'pin 138 (gpio4-10): febf0020.pwm' in claims and 'group pwm14m1-pins' in claims
assert 'pin 114 (gpio3-18): febf0020.pwm' not in claims, 'Refuse playback on old motor/backlight mux'
"""
assert text.count(anchor)==1;text=text.replace(anchor,anchor+guard)
anchor="try:\n    result['output_gain']"
assert text.count(anchor)==1
text=text.replace(anchor,"try:\n    result['speaker_route']=cmd(['amixer','-c','0','sset','Speaker','on'])\n    result['output_gain']")
runner.write_text(text)
r=subprocess.run(['python3',str(P/'tools/ssh-f8-desktop.py'),'--address','192.168.1.227','--script',str(runner),'--sudo'],capture_output=True,text=True,timeout=100)
assert r.returncode==0,r.stderr[-1300:]
d=json.loads(r.stdout);d['correct_backlight_mux_checked_before_playback']=True
out.write_text(json.dumps(d,indent=2)+'\n')
print(json.dumps({k:d.get(k) for k in ['boot_id','speaker_route','output_gain','output_route','play','restore','sound_log']},indent=2))
