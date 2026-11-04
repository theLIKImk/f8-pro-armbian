import fcntl,json,os,struct,subprocess
from pathlib import Path
assert os.geteuid()==0 and os.environ.get('SUDO_USER')=='likimk'
p=next(p for p in Path('/sys/class/input').glob('event*') if (p/'device/name').read_text().strip()=='f8-gsl-shuping')
fd=os.open('/dev/input/'+p.name,os.O_RDONLY|os.O_NONBLOCK|os.O_CLOEXEC);out={'device':p.name,'axes':{}}
try:
 for name,code in [('slots',0x2f),('x',0x35),('y',0x36),('tracking_id',0x39)]:
  data=bytearray(24);fcntl.ioctl(fd,(2<<30)|(24<<16)|(ord('E')<<8)|(0x40+code),data,True)
  current,minimum,maximum,fuzz,flat,resolution=struct.unpack('6i',data)
  out['axes'][name]={'minimum':minimum,'maximum':maximum,'resolution':resolution}
finally:os.close(fd)
r=subprocess.run(['udevadm','info','--query=property','--path',str(p.resolve())],capture_output=True,text=True,timeout=8);out['udev']=r.stdout
u=['runuser','-u','likimk','--','env','XDG_RUNTIME_DIR=/run/user/1602','DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1602/bus','WAYLAND_DISPLAY=wayland-0','QT_QPA_PLATFORM=wayland']
r=subprocess.run(u+['kscreen-doctor','-o'],capture_output=True,text=True,timeout=10);out['screen']=r.stdout;out['screen_errors']=r.stderr
print(json.dumps(out,indent=2))
