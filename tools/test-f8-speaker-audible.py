import json,pwd,subprocess,os,math,array,shutil
u=['runuser','-u','likimk','--','env','XDG_RUNTIME_DIR=/run/user/1602','DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1602/bus']
a=array.array('f',(0.2*math.sin(2*math.pi*440*i/48000) for i in range(48000) for ch in range(2)))
r=subprocess.run(u+['pw-cat','--playback','--raw','--target=f8-speaker-volume','--rate=48000','--channels=2','--format=f32','-'],input=a.tobytes(),capture_output=True,timeout=10)
print(json.dumps({'test_exit':r.returncode,'stderr':r.stderr.decode(),'gcc':shutil.which('gcc'),'ladspa_header':os.path.isfile('/usr/include/ladspa.h')}))
