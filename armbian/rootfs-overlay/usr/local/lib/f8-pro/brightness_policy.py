"""Conservative relative-light brightness policy. No claim of lux calibration."""
import math

def target_percent(raw,dark=3,indoor=12,bias=0):
    net=max(0,raw-dark);reference=max(1,indoor-dark)
    # Indoor reference 35%; each factor of 4 adds 18 percentage points.
    return max(12,min(90,35+18*math.log((net+reference*.25)/(reference*1.25),4)+bias))

class BrightnessPolicy:
    def __init__(self):
        self.filtered=None;self.last=None;self.last_set=None;self.pause_until=0;self.last_write=-1e9
    def update(self,raw,current,now,enabled=True,blocked=False,dark=3,indoor=12,bias=0):
        if not enabled or blocked:
            self.last=None;self.last_set=None;return None
        dt=0 if self.last is None else max(0,min(1,now-self.last));self.last=now
        desired=target_percent(raw,dark,indoor,bias)
        self.filtered=desired if self.filtered is None else self.filtered+(desired-self.filtered)*(1-math.exp(-dt/3))
        # A KDE/manual change outside our pending brightness pauses automation for 60s.
        if self.last_set is not None and abs(current-self.last_set)>2:
            self.pause_until=now+60;self.last_set=None
        if now<self.pause_until:return None
        if abs(self.filtered-current)<2 or now-self.last_write<.12:return None
        step=max(-.4,min(.4,self.filtered-current));result=current+step
        if abs(result-current)<.01:return None
        self.last_set=result;self.last_write=now;return result
