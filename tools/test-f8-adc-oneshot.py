"""Exercise exact ADC wire messages and refusal paths without a device."""
import importlib.util
import json
from pathlib import Path
P=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('adc',P/'armbian/power/bq-adc-oneshot.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class Fixture:
    def __init__(self,control=0x1c,pn=3,stuck=False):
        self.raw={i:0 for i in range(21)};self.raw.update({2:control,14:95,17:0x9a,18:20,20:pn<<3})
        self.writes=[];self.stuck=stuck;self.clock=0;self.started=False
    def ioctl(self,fd,cmd,request):
        assert cmd==0x0707
        messages=request.msgs
        if request.nmsgs==1:
            msg=messages[0];assert msg.addr==0x6a and msg.flags==0 and msg.len==2
            assert msg.buf[0]==2 and msg.buf[1]==(self.raw[2]|0x80)
            assert (msg.buf[1]^self.raw[2])==0x80
            self.raw[2]=msg.buf[1];self.writes.append((2,msg.buf[1]));self.started=True
        else:
            a,b=messages[0],messages[1]
            assert request.nmsgs==2 and a.addr==b.addr==0x6a
            assert a.flags==0 and a.len==1 and b.flags==1
            start=a.buf[0];assert not(start<=12<start+b.len)
            if self.started and not self.stuck:self.raw[2]&=0x7f
            for index in range(b.len):b.buf[index]=self.raw[start+index]
        return request.nmsgs
    def now(self):return self.clock
    def sleep(self,seconds):self.clock+=seconds
def run(f):return m.measure(m.Bus(-1,f.ioctl),f.now,f.sleep)
f=Fixture();r=run(f)
assert r['complete'] and r['configuration_unchanged'] and f.writes==[(2,0x9c)]
assert r['measurement']['vbus_uv']==5200000 and r['measurement']['battery_charge_adc_ma']==1000
for control in [0x9c,0x5c,0x1e]:
    f=Fixture(control=control);assert not run(f)['complete'] and not f.writes
f=Fixture(pn=7);assert not run(f)['complete'] and not f.writes
f=Fixture(stuck=True);assert not run(f)['complete'] and len(f.writes)==1
try:m.Bus(-1,Fixture().ioctl).read(12,1)
except ValueError:pass
else:raise AssertionError('Fault latch was allowed')
out=P/'analysis/armbian/live-g6/adc-oneshot-fixtures.json'
out.write_text(json.dumps({'passed':True,'single_strobe_only':True,'other_control_bits_preserved':True,
 'busy_continuous_dpdm_and_wrong_part_refused':True,'timeout_no_extra_write':True,'fault_latch_skipped':True},indent=2)+'\n')
print('PASS: exact single ADC strobe, policy bits preserved, timeout/refusal/fault-latch checks')
