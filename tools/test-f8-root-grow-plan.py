from pathlib import Path
import importlib.util,unittest
P=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('grow',P/'armbian/first-run/root-grow-r1a.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class Test(unittest.TestCase):
 def info(self):return dict(source=m.DEV,fstype='ext4',uuid=m.UUID,partuuid=m.PARTUUID,start=m.START,sectors=m.SECTORS,sector_size=512,errors=0,blocks=12*1024**3//4096,block_size=4096)
 def test_target_and_noop(self):
  i=self.info();p=m.plan(i);self.assertTrue(p['grow']);self.assertEqual(p['target_bytes'],246960619520)
  i['blocks']=p['target_bytes']//4096;self.assertFalse(m.plan(i)['grow'])
 def test_every_identity_and_geometry_guard(self):
  for k,v in dict(source='/dev/sda',fstype='xfs',uuid='wrong',partuuid='wrong',start=0,sectors=1,sector_size=4096,errors=1,block_size=1024,blocks=10**12).items():
   with self.subTest(key=k):
    with self.assertRaises(ValueError):m.plan(dict(self.info(),**{k:v}))
if __name__=='__main__':unittest.main()
