import importlib.util,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'armbian/power'))
import performance_state as state
spec=importlib.util.spec_from_file_location('performance_apply',P/'armbian/power/performance-apply.py');helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
class Controls(unittest.TestCase):
 def setUp(self):self.s={'key':'gpu','enabled':True,'allowed':[200000000,300000000,400000000],'governors':['simple_ondemand','performance']}
 def test_reject_unvalidated_or_wrong_units(self):
  for lo,hi in [(1000000000,1000000000),(200,400),(400000000,200000000),(True,400000000)]:
   with self.assertRaises(ValueError):state.validate(self.s,'range',lo,hi)
 def test_fixed_requires_one_frequency(self):
  with self.assertRaises(ValueError):state.validate(self.s,'fixed',200000000,400000000)
 def test_unknown_mode_and_missing_governor(self):
  with self.assertRaises(ValueError):state.validate(self.s,'turbo')
  self.s['governors']=['performance']
  with self.assertRaises(ValueError):state.validate(self.s,'auto')
 def test_auto_uses_validated_range(self):
  p=state.validate(self.s,'auto',1000000000,1000000000)
  self.assertEqual((p['minimum'],p['maximum'],p['governor']),(200000000,400000000,'simple_ondemand'))
 def test_transaction_restores_first_device_on_second_failure(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t);gpu=root/'gpu';cpu=root/'cpu';gpu.mkdir();cpu.mkdir()
   for p,g in [(gpu,True),(cpu,False)]:
    for n,v in [('min_freq' if g else 'scaling_min_freq','200'),('max_freq' if g else 'scaling_max_freq','400'),('governor' if g else 'scaling_governor','simple_ondemand' if g else 'ondemand')]: (p/n).write_text(v)
   devices={'gpu':('GPU',gpu,1,400),'cpu0':('CPU',cpu,1,400)}
   def snap(k):
    p=devices[k][1];g=k=='gpu'
    return dict(key=k,enabled=True,allowed=[200,300,400],governors=['simple_ondemand' if g else 'ondemand'],minimum=int((p/('min_freq' if g else 'scaling_min_freq')).read_text()),maximum=int((p/('max_freq' if g else 'scaling_max_freq')).read_text()),governor=(p/('governor' if g else 'scaling_governor')).read_text())
   original=helper.write_range
   def fail_second(p,lo,hi,g):
    if p==cpu and lo==300:raise OSError('simulated kernel rejection')
    return original(p,lo,hi,g)
   with patch.object(helper,'DEVICES',devices),patch.object(helper,'snapshot',snap),patch.object(helper,'write_range',fail_second):
    with self.assertRaises(OSError):helper.apply([{'key':'gpu','mode':'fixed','minimum':300,'maximum':300},{'key':'cpu0','mode':'fixed','minimum':300,'maximum':300}])
   self.assertEqual((snap('gpu')['minimum'],snap('gpu')['maximum']),(200,400))
if __name__=='__main__':unittest.main()
