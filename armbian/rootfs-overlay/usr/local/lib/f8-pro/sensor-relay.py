#!/usr/bin/python3
"""User-session measured sensor relay, fusion D-Bus/JSON and optional automatic brightness."""
import os,json,time,math,struct,signal,traceback
from pathlib import Path
import dbus,dbus.service
from dbus.mainloop.glib import DBusGMainLoop
from gi.repository import GLib
from relay_reading import read_device,read_magnet,example_matrix
from sensor_fusion import MotionFusion,board_magnet
from brightness_policy import BrightnessPolicy
from gyro_stabilizer import load_shared_bias

DBusGMainLoop(set_as_default=True)
ROOT=Path.home()/'.config/f8-pro';ROOT.mkdir(parents=True,exist_ok=True)
RUNTIME=Path(os.environ['XDG_RUNTIME_DIR']);CONFIG=ROOT/'sensor-relay.json'
def read_json(p,default):
    try:return json.loads(p.read_text())
    except (OSError,ValueError):return default

def atomic(p,d):
    tmp=p.with_suffix('.tmp');fd=os.open(tmp,os.O_WRONLY|os.O_CREAT|os.O_TRUNC,0o600)
    with os.fdopen(fd,'w') as f:json.dump(d,f,ensure_ascii=False,allow_nan=False)
    os.replace(tmp,p)

class Relay(dbus.service.Object):
    def __init__(self,bus):
        self.name=dbus.service.BusName('net.f8.Sensors',bus=bus);super().__init__(bus,'/net/f8/Sensors')
        self.bus=bus;self.fusion=MotionFusion();self.policy=BrightnessPolicy();self.state={'online':False};self.devices={};self.scan_at=0;self.mag_at=0;self.mag={};self.opt_at=0;self.opt={};self.report_at=0;self.feed=None;self.brightness_at=0;self.bright=None;self.near=None;self.cal_at=0;self.cal={};self.bias_samples=[];self.gyro_bias=(0,0,0);self.config={'relay_enabled':True,'auto_brightness':True,'brightness_bias_percent':0};self.config.update(read_json(CONFIG,{}));self.save()
        self.power=None
        GLib.timeout_add(50,self.tick)
    def save(self):atomic(CONFIG,self.config)
    @dbus.service.method('net.f8.Sensors1',in_signature='',out_signature='s')
    def GetSnapshot(self):return json.dumps(self.state,allow_nan=False)
    @dbus.service.method('net.f8.Sensors1',in_signature='',out_signature='s')
    def GetSettings(self):return json.dumps(self.config)
    @dbus.service.method('net.f8.Sensors1',in_signature='b',out_signature='')
    def SetAutoBrightness(self,value):
        self.config['auto_brightness']=bool(value);self.policy=BrightnessPolicy();self.save()
    @dbus.service.method('net.f8.Sensors1',in_signature='b',out_signature='')
    def SetRelayEnabled(self,value):
        self.config['relay_enabled']=bool(value)
        if not value and self.feed is not None:os.close(self.feed);self.feed=None
        self.fusion.reset();self.save()
    @dbus.service.method('net.f8.Sensors1',in_signature='d',out_signature='')
    def SetBrightnessBias(self,value):
        v=float(value)
        if not math.isfinite(v) or abs(v)>25:raise ValueError('Bias must be within -25..25')
        self.config['brightness_bias_percent']=v;self.save()
    @dbus.service.signal('net.f8.Sensors1',signature='s')
    def Sample(self,snapshot):pass
    def discover(self,now):
        if now-self.scan_at<5:return
        self.scan_at=now;self.devices={}
        for p in Path('/sys/bus/iio/devices').glob('iio:device*'):
            try:
                n=(p/'name').read_text().strip()
                if n in ['mpu6500','AK8963','f8-em30918']:self.devices[n]=p
            except OSError:pass
        if 'mpu6500' in self.devices:self.matrix,self.matrix_source=example_matrix(self.devices['mpu6500'])
    def optical(self,now):
        if now-self.cal_at>2:self.cal_at=now;self.cal=read_json(ROOT/'optical-calibration.json',{});self.gyro_bias=load_shared_bias() or (0,0,0)
        if now-self.opt_at<.2:return
        self.opt_at=now;p=self.devices.get('f8-em30918')
        self.opt={'available':False,'monotonic':now}
        if p:
            try:
                raw=int((p/'in_intensity_raw').read_text());ps=int((p/'proximity_raw').read_text());c=self.cal
                far=c.get('far');near=c.get('near')
                if isinstance(far,(int,float)) and isinstance(near,(int,float)) and 0<=far<near<=255 and near-far>=10:
                    if ps>=far+.65*(near-far):self.near=True
                    elif ps<=far+.35*(near-far):self.near=False
                self.opt.update(available=True,ambient_raw=raw,proximity_raw=ps,near=self.near,ambient_units='raw ADC, not lux',proximity_units='raw ADC, not cm')
            except (OSError,ValueError) as e:self.opt['error']=str(e)
    def adjust_brightness(self,now):
        if now-self.brightness_at<.12:return
        self.brightness_at=now
        try:
            if self.power is None:self.power=dbus.Interface(self.bus.get_object('org.kde.Solid.PowerManagement','/org/kde/Solid/PowerManagement/Actions/BrightnessControl'),'org.kde.Solid.PowerManagement.Actions.BrightnessControl')
            maximum=int(self.power.brightnessMax(timeout=1));current=int(self.power.brightness(timeout=1));self.bright={'current_percent':round(current/maximum*100,1)}
            blocked=False
            try:blocked=bool(dbus.Interface(self.bus.get_object('org.freedesktop.ScreenSaver','/ScreenSaver'),'org.freedesktop.ScreenSaver').GetActive(timeout=1))
            except dbus.DBusException:blocked=True
            cover=read_json(Path.home()/'.cache/f8-cover/status.json',{})
            # Preserve cover-off, dimming and screen-lock policy. Never wake a display.
            if cover.get('closed') or cover.get('covered'):blocked=True
            b=Path('/sys/class/backlight/backlight')
            if (b/'bl_power').exists() and int((b/'bl_power').read_text())!=0:blocked=True
            enabled=bool(self.config['auto_brightness']) and self.opt.get('available',False)
            c=self.cal;dark=c.get('ambient_dark_raw',3);indoor=c.get('ambient_indoor_raw',12)
            target=self.policy.update(self.opt.get('ambient_raw',0),current/maximum*100,now,enabled,blocked,dark,indoor,self.config.get('brightness_bias_percent',0))
            if target is not None:self.power.setBrightnessSilent(dbus.Int32(round(target/100*maximum)),timeout=1)
            self.bright.update(enabled=self.config['auto_brightness'],blocked=blocked,target_percent=self.policy.filtered,manual_pause_seconds=max(0,round(self.policy.pause_until-now)),error=None)
        except Exception as e:self.power=None;self.bright={'enabled':self.config['auto_brightness'],'error':str(e)}
    def tick(self):
        now=time.monotonic()
        try:
            self.discover(now);self.optical(now)
            if not self.config['relay_enabled']:
                self.adjust_brightness(now)
                self.state={'version':1,'online':True,'valid':False,'relay_enabled':False,'monotonic':now,'brightness':self.bright,'status':'兼容中继已关闭；自动亮度独立运行'}
                if now-self.report_at>=.2:
                    self.report_at=now;atomic(RUNTIME/'f8-sensor-relay.json',self.state);self.Sample(json.dumps(self.state,allow_nan=False))
                return True
            p=self.devices.get('mpu6500')
            if not p:raise OSError('MPU6500 not available')
            raw=read_device(p);a=raw['scaled'].get('accel');w=raw['scaled'].get('anglvel')
            if a is None or w is None:raise OSError('; '.join(raw['errors']))
            mapped=lambda v:[sum(row[i]*v[i] for i in range(3)) for row in self.matrix]
            a=mapped(a);w=mapped(w)
            if now-self.mag_at>=.4:
                self.mag_at=now;mp=self.devices.get('AK8963');self.mag=read_magnet(mp,raw['scaled']['accel']) if mp else {}
            fusion=self.fusion.advance(a,w,raw['monotonic'],self.mag,self.gyro_bias)
            if self.feed is None:
                try:self.feed=os.open('/dev/f8-sensor-feed',os.O_WRONLY|os.O_CLOEXEC)
                except OSError:pass
            feed_error=None
            if self.feed is not None:
                try:
                    # Chromium negates Linux acceleration; relay uses Linux gravity sign.
                    values=[-v for v in a]+list(fusion.get('corrected_angular_velocity_rad_s',w))
                    mag_valid=bool(fusion.get('absolute_valid')) and not fusion.get('mag_prediction_only') and self.mag.get('corrected_ut') is not None
                    m=board_magnet(self.mag['corrected_ut']) if mag_valid else (0,0,0)
                    # Match the shared 180-degree heading convention in standard IIO magnetic axes.
                    m=(-m[0],-m[1],m[2]);values+=list(m)
                    os.write(self.feed,struct.pack('=9iI',*(round(v*1e6) for v in values),int(mag_valid)))
                except OSError as e:feed_error=str(e);os.close(self.feed);self.feed=None
            self.adjust_brightness(now)
            self.state={**fusion,'version':1,'online':True,'relay_enabled':True,'monotonic':raw['monotonic'],'acceleration_m_s2':a,'angular_velocity_rad_s':fusion.get('corrected_angular_velocity_rad_s',w),'magnetic':self.mag,'optical':self.opt,'brightness':self.bright,'iio_feed_connected':self.feed is not None,'iio_feed_error':feed_error,'matrix_source':self.matrix_source,'source':'live physical F8 IIO; session calibration'}
        except Exception as e:self.state={'version':1,'online':False,'valid':False,'monotonic':now,'error':str(e),'brightness':self.bright}
        if now-self.report_at>=.2:
            self.report_at=now;atomic(RUNTIME/'f8-sensor-relay.json',self.state);self.Sample(json.dumps(self.state,allow_nan=False))
        return True
    def close(self):
        self.state.update(online=False,valid=False,monotonic=time.monotonic());atomic(RUNTIME/'f8-sensor-relay.json',self.state)
        if self.feed is not None:os.close(self.feed)

bus=dbus.SessionBus();relay=Relay(bus);loop=GLib.MainLoop()
def stop(*args):relay.close();loop.quit()
for sig in [signal.SIGTERM,signal.SIGINT]:signal.signal(sig,stop)
loop.run()
