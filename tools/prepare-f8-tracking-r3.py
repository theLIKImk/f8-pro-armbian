import argparse,base64,json
from pathlib import Path
P=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--round',choices=['r3','r4','r5'],default='r3');args=parser.parse_args()
raw=(P/'armbian/touch/capture-tracking.py').read_text(encoding='utf-8').replace("touch-diagnostic/r2", "touch-diagnostic/r3").replace('deadline=start+65','deadline=start+35')
app=(P/'armbian/touch/multitouch-test.py').read_text(encoding='utf-8')
old="steps=[(5,'准备：请抬起所有手指'),(13,'单指：一根手指在蓝色区域缓慢画圈'),(16,'全部抬起，准备双指'),(25,'双指：两根手指按住并缓慢移动'),(28,'全部抬起，准备逐根五指'),(45,'逐根五指：每隔1秒放下一指，然后一起缓慢移动'),(48,'全部抬起，准备同时五指'),(60,'同时五指：五指一起按下并缓慢移动'),(65,'全部抬起，诊断即将完成')]"
new="steps=[(4,'准备：抬起所有手指'),(14,'五指张开：逐根放下，然后缓慢移动'),(17,'全部抬起，准备靠近测试'),(30,'五指靠近：逐根放下，缓慢靠近但指尖不要互相接触'),(35,'全部抬起，诊断即将完成')]"
if args.round=='r5':
 new="steps=[(4,'准备：抬起所有手指'),(17,'四指快速敲击：间隔2至3厘米，反复短按并全部抬起'),(20,'全部抬起，准备靠近测试'),(32,'五指靠近：逐根放下，靠近并缓慢移动'),(35,'全部抬起，诊断即将完成')]"
assert old in app
app=app.replace(old,new).replace('trace-r2.jsonl','trace-r3.jsonl').replace('开始同步诊断（65秒）','开始近距离诊断（35秒）')
files={
 '/var/lib/f8-pro/touch-diagnostic/capture-tracking-r3.py':raw,
 '/var/lib/f8-pro/touch-diagnostic/capture-algorithm-r3.py':(P/'armbian/touch/capture-algorithm.py').read_text(encoding='utf-8'),
 '/usr/local/lib/f8-pro/multitouch-test.py':app,
}
files={k.replace('r3',args.round):v.replace('r3',args.round) for k,v in files.items()}
payload=base64.b64encode(json.dumps(files).encode()).decode()
code='''import base64,json,os,subprocess,time
from pathlib import Path
assert os.geteuid()==0 and os.environ.get('SUDO_USER')=='likimk'
assert not Path('/var/lib/f8-pro/touch-diagnostic/r3/algorithm-input.txt').exists(),'Preserve existing R3 evidence'
u=['runuser','-u','likimk','--','env','XDG_RUNTIME_DIR=/run/user/1602','DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1602/bus','WAYLAND_DISPLAY=wayland-0','QT_QPA_PLATFORM=wayland']
stop=subprocess.run(u+['systemctl','--user','stop','f8-multitouch-test.service'],capture_output=True,text=True,timeout=8);assert stop.returncode in [0,5],stop.stderr
files=json.loads(base64.b64decode(PAYLOAD))
for dest,s in files.items():
 p=Path(dest);assert not p.is_symlink();p.write_text(s);p.chmod(0o755 if dest.startswith('/usr/local') else 0o700)
flag=Path('/run/f8-touch-diagnostic/start');assert not flag.is_symlink();flag.write_text('0');os.chown(flag,1602,1602);flag.chmod(0o600)
r=subprocess.run(['systemd-run','--collect','--unit=f8-touch-capture-r3','--property=RuntimeMaxSec=380','/usr/bin/python3','/var/lib/f8-pro/touch-diagnostic/capture-algorithm-r3.py'],capture_output=True,text=True,timeout=8);assert r.returncode==0,r.stderr
time.sleep(1)
ready=json.loads(Path('/var/lib/f8-pro/touch-diagnostic/r3/summary.json').read_text());assert ready['phase']=='waiting_for_user_button',ready
r=subprocess.run(u+['systemd-run','--user','--collect','--unit=f8-multitouch-test','/usr/bin/python3','/usr/local/lib/f8-pro/multitouch-test.py'],capture_output=True,text=True,timeout=8);assert r.returncode==0,r.stderr
print(json.dumps({'capture_ready':ready,'app':r.stderr}))
'''.replace('r3',args.round).replace('PAYLOAD',repr(payload))
(P/('local/hardware/multitouch-'+args.round+'-runner.py')).write_text(code,encoding='utf-8')
