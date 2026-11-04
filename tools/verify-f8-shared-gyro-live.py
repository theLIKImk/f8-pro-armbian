from pathlib import Path
import subprocess,json,time,math
pre=['runuser','-u','likimk','--','env','XDG_RUNTIME_DIR=/run/user/1602','DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1602/bus']
c=Path('/home/likimk/.config/f8-pro/sensor-relay.json');settings=json.loads(c.read_text());original=settings['relay_enabled']
def toggle(v):subprocess.run(pre+['gdbus','call','--session','--dest','net.f8.Sensors','--object-path','/net/f8/Sensors','--method','net.f8.Sensors1.SetRelayEnabled','true' if v else 'false'],check=True,capture_output=True)
try:
 toggle(True);time.sleep(3);samples=[]
 for _ in range(30):
  s=json.loads(Path('/run/user/1602/f8-sensor-relay.json').read_text());samples.append(s);time.sleep(.1)
 cal=json.loads(Path('/run/user/1602/f8-gyro-bias.json').read_text())
 o={'shared_calibration_present':True,'relay_loaded_shared_bias':all(s.get('gyro_manual_bias_rad_s')==cal['bias_rad_s'] for s in samples),'samples':len(samples),'valid':sum(bool(s.get('valid')) for s in samples),'stationary_samples':sum(bool(s.get('gyro_stationary')) for s in samples),'peak_corrected_gyro_rad_s':max(math.sqrt(sum(v*v for v in s['angular_velocity_rad_s'])) for s in samples),'observer':json.loads(Path('/run/user/1602/f8-sensor-fusion.json').read_text()),'calibration_file_mode':oct(Path('/run/user/1602/f8-gyro-bias.json').stat().st_mode&0o777)}
finally:toggle(original)
o['settings_restored']=json.loads(c.read_text())==settings
print(json.dumps(o))
