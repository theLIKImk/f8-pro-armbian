"""Read-only tap of the AIQ process's own mmap'ed ISP parameter buffers."""
import argparse,subprocess
from pathlib import Path
P=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--live',action='store_true');args=parser.parse_args()
s=(P/'local/hardware/camera-c4-aiq-wb-api-runner.sh').read_text()
s=s.replace('back-aiq-fps14-apiwb.log','back-aiq-param-tap.log').replace('back-aiq-fps14-apiwb-640x480.nv12','back-aiq-param-tap-640x480.nv12')
anchor="root=Path('/opt/f8-pro-camera/aiq-v6-c4');folder=Path('/run/f8-camera-c4')\n"
install='''import hashlib
tap=root/'lib/libf8-aiq-param-tap.so';assert not tap.exists()
data=Path('/home/f8test/.cache/f8-camera-aiq-c4-stage/libf8-aiq-param-tap.so').read_bytes()
assert hashlib.sha256(data).hexdigest()=='9d55e9d67b1eed995052a3d8048c7798c82be5e86cf50f323ddb26c04fcadf1f'
tap.write_bytes(data);tap.chmod(0o644)
'''
s=s.replace(anchor,anchor+install)
s=s.replace("stderr=subprocess.STDOUT,start_new_session=True)","stderr=subprocess.STDOUT,start_new_session=True,env={**os.environ,'LD_PRELOAD':str(tap)})")
s=s.replace("print('STOP',lib.rk_aiq_uapi2_sysctl_stop(ctx,False),flush=True)","print('PARAM_BUFFERS',C.CDLL('/opt/f8-pro-camera/aiq-v6-c4/lib/libf8-aiq-param-tap.so').f8_dump_params(),flush=True)\n    print('STOP',lib.rk_aiq_uapi2_sysctl_stop(ctx,False),flush=True)")
suffix='param-tap-live' if args.live else 'param-tap'
if args.live:
    s=s.replace('assert not tap.exists()','assert tap.exists()').replace('tap.write_bytes(data);tap.chmod(0o644)','assert tap.read_bytes()==data')
    s=s.replace('back-aiq-param-tap.log','back-aiq-param-tap-live.log').replace('back-aiq-param-tap-640x480.nv12','back-aiq-param-tap-live-640x480.nv12')
    dump="print('PARAM_BUFFERS',C.CDLL('/opt/f8-pro-camera/aiq-v6-c4/lib/libf8-aiq-param-tap.so').f8_dump_params(),flush=True)"
    s=s.replace('    '+dump+'\n','')
    s=s.replace('    time.sleep(18)',"    import threading\n    timer=threading.Timer(1.0,lambda: "+dump+")\n    timer.start()\n    time.sleep(18)")
r=P/f'local/hardware/camera-c4-aiq-{suffix}-runner.sh';assert not r.exists();r.write_text(s)
p=subprocess.run(['python3',str(P/'tools/ssh-f8-desktop.py'),'--address','192.168.1.227','--script',str(r),'--sudo'],capture_output=True,text=True,timeout=90)
assert p.returncode==0,p.stderr
(P/f'local/hardware/camera-c4-aiq-{suffix}-test01.json').write_text(p.stdout)
print('Saved parameter tap trial')
