"""Wire-protocol and ADC mode restoration fixtures, no hardware access."""
import importlib.util
import json
from pathlib import Path
P=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('audit',P/'armbian/power/bq-adc-audit.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class Fixture:
    def __init__(self,fail=False):
        self.raw={i:0 for i in range(21)};self.raw.update({2:0x1c,11:22,14:91,17:150,18:24,20:31})
        self.writes=[];self.fail=fail;self.failed=False
    def ioctl(self,fd,cmd,req):
        assert cmd==0x707
        if req.nmsgs==1:
            a=req.msgs[0];assert a.addr==0x6a and a.flags==0 and a.len==2
            reg,value=a.buf[0],a.buf[1];assert reg==2 and (self.raw[2]^value)&0x3f==0
            assert not value&0x80;self.raw[2]=value;self.writes.append(value)
        else:
            a,b=req.msgs[0],req.msgs[1];assert req.nmsgs==2 and a.len==1 and b.flags==1 and a.addr==b.addr==0x6a
            start=a.buf[0];assert not(start<=12<start+b.len)
            if self.fail and self.raw[2]&0x40 and start==18 and not self.failed:
                self.failed=True;raise OSError('Injected read failure')
            for i in range(b.len):b.buf[i]=self.raw[start+i]
        return req.nmsgs
for fail in [False,True]:
    f=Fixture(fail);r=m.audit(m.Bus(-1,f.ioctl),lambda seconds:None)
    assert f.writes==[0x5c,0x1c] and r['restored'] and f.raw[2]==0x1c
    assert r['complete']==(not fail)
for ctrl in [0x9c,0x5c,0x1e]:
    f=Fixture();f.raw[2]=ctrl;r=m.audit(m.Bus(-1,f.ioctl),lambda seconds:None)
    assert not f.writes and not r['complete']
f=Fixture()
try:m.Bus(-1,f.ioctl).adc_mode(0x1c,0x5d)
except ValueError:pass
else:raise AssertionError('Policy change accepted')
out=P/'analysis/armbian/live-g6/adc-audit-fixtures.json'
out.write_text(json.dumps({'passed':True,'restore_on_success_and_read_error':True,'mode_bits_only':True,
 'busy_mode_and_policy_changes_refused':True,'fault_register_skipped':True},indent=2)+'\n')
print('PASS: continuous/byte audit, exact mode-only writes, restoration on read error')
