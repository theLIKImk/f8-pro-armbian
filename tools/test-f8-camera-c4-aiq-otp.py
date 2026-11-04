"""Test auto AE/AWB with invalid-OTP rejection and fixed14fps, isolated to AIQ."""
import argparse,subprocess
from pathlib import Path
P=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--user-long',action='store_true');parser.add_argument('--sample',type=int,default=1);args=parser.parse_args();assert 1<=args.sample<=9
s=(P/'local/hardware/camera-c4-aiq-fps14-runner.sh').read_text()
s=s.replace("derived=root/'iqfiles-fps14';assert not derived.exists();derived.mkdir()","derived=root/'iqfiles-fps14';assert derived.is_dir()")
s=s.replace("(derived/name).write_text(json.dumps(changed)+'\\n')","assert json.loads((derived/name).read_text())==changed")
s=s.replace('back-aiq-fps14.log','back-aiq-fps14-otp.log').replace('back-aiq-fps14-640x480.nv12','back-aiq-fps14-otp-640x480.nv12')
anchor="root=Path('/opt/f8-pro-camera/aiq-v6-c4');folder=Path('/run/f8-camera-c4')\n"
install='''import hashlib
shim=root/'lib/libf8-aiq-otp.so';assert not shim.exists()
data=Path('/home/f8test/.cache/f8-camera-aiq-c4-stage/libf8-aiq-otp.so').read_bytes()
assert hashlib.sha256(data).hexdigest()=='8993fc7ed9759ca49aa7a6c38050700b125b18c55d6079bce28f6de910915f2b'
shim.write_bytes(data);shim.chmod(0o644)
'''
s=s.replace(anchor,anchor+install)
s=s.replace('stderr=subprocess.STDOUT,start_new_session=True)',"stderr=subprocess.STDOUT,start_new_session=True,env={**os.environ,'LD_PRELOAD':str(shim)})")
suffix='otp-user-long' if args.user_long else 'otp'
if args.user_long:
    s=s.replace('assert not shim.exists()','assert shim.exists()').replace('shim.write_bytes(data);shim.chmod(0o644)','assert shim.read_bytes()==data')
    s=s.replace("folder=Path('/run/f8-camera-c4')","folder=Path('/home/f8test/.cache/f8-camera-aiq-c4-stage')")
    s=s.replace('back-aiq-fps14-otp.log','back-aiq-fps14-otp-user-long.log').replace('back-aiq-fps14-otp-640x480.nv12','back-aiq-fps14-otp-user-long-640x480.nv12')
    s=s.replace("'--stream-count=45'","'--stream-count=140'").replace('timeout=10)','timeout=15)')
    s=s.replace("out['bytes']=len(data);out['frames']=len(data)/460800", "out['bytes']=len(data);out['frames']=len(data)/460800\n            out['mean_y_samples']=[round(sum(data[i:i+307200])/307200,2) for i in range(0,len(data),460800*28) if i+460800<=len(data)]\n            target.write_bytes(data[-460800:]);out['retained_last_frame_bytes']=min(len(data),460800)")
    # Ordinary user dmesg access may be restricted. Capture it separately as root.
    s=s.replace("out['dmesg_tail']=subprocess.check_output(['dmesg'],text=True).splitlines()[-50:]", "out['dmesg_tail']=[]")
if args.sample!=1:
    assert args.user_long
    suffix+=f'-{args.sample:02d}'
    s=s.replace('back-aiq-fps14-otp-user-long',f'back-aiq-fps14-otp-user-long-{args.sample:02d}')
r=P/f'local/hardware/camera-c4-aiq-{suffix}-runner.sh';assert not r.exists();r.write_text(s)
cmd=['python3',str(P/'tools/ssh-f8-desktop.py'),'--address','192.168.1.227','--script',str(r)]
if not args.user_long:cmd.append('--sudo')
p=subprocess.run(cmd,capture_output=True,text=True,timeout=90)
assert p.returncode==0,p.stderr
(P/f'local/hardware/camera-c4-aiq-{suffix}-test01.json').write_text(p.stdout)
print('Saved invalid-OTP rejection trial')
