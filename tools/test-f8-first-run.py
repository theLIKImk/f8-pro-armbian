"""Meaningful validation and failure/retry tests without touching host accounts."""
import importlib.util,json,subprocess,tempfile,unittest
from pathlib import Path
P=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('setup_apply',P/'armbian/first-run/first-run-apply.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class Tests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
  for p in ['etc/skel/.config','usr/share/zoneinfo/Asia']: (self.root/p).mkdir(parents=True,exist_ok=True)
  (self.root/'etc/skel/.config/board-default').write_text('test-default')
  (self.root/'etc/skel/.config/enabled-link').symlink_to('board-default')
  (self.root/'etc/passwd').write_text('root:x:0:0::/root:/bin/bash\nf8setup:x:1601:1601::/home/f8setup:/bin/bash\n')
  (self.root/'etc/f8-pro-release-r1').touch();(self.root/'usr/share/zoneinfo/Asia/Hong_Kong').write_bytes(b'TZif-test')
  self.data=dict(username='demo',fullname='测试用户',password='example-only-123',locale='zh_CN.UTF-8',timezone='Asia/Hong_Kong',hostname='f8-pad',autologin=False)
  self.calls=[]
 def tearDown(self):self.tmp.cleanup()
 def run_cmd(self,args,**kw):
  self.calls.append((args,kw))
  if args[0].endswith('/useradd') and '-m' in args:
   import shutil
   shutil.copytree(self.root/'etc/skel',self.root/'home'/args[-1],symlinks=True)
  if args[0].endswith('/userdel'):
   import shutil
   shutil.rmtree(self.root/'home'/args[-1],ignore_errors=True)
  return subprocess.CompletedProcess(args,0)
 def test_reject_invalid_before_any_command(self):
  for key,value in [('username','../root'),('username','root'),('username','f8setup'),('password','abc\nroot:bad'),('password','abc:defgh'),('locale','evil'),('timezone','../../etc/passwd'),('timezone','/etc/passwd'),('hostname','x\nuser'),('autologin','false')]:
   with self.subTest(key=key,value=value):
    with self.assertRaises(ValueError):m.apply(dict(self.data,**{key:value}),self.root,self.run_cmd)
  self.assertEqual(self.calls,[])
 def test_success_single_use_and_no_password_saved(self):
  self.assertTrue(m.apply(self.data,self.root,self.run_cmd)['ok'])
  self.assertEqual((self.root/'home/demo/.config/board-default').read_text(),'test-default')
  self.assertTrue((self.root/'home/demo/.config/enabled-link').is_symlink())
  text=(self.root/'etc/sddm.conf.d/99-f8-first-run.conf').read_text();self.assertIn('User=\n',text)
  self.assertEqual((self.root/'etc/localtime').readlink(),Path('/usr/share/zoneinfo/Asia/Hong_Kong'))
  for f in self.root.rglob('*'):
   if f.is_file() and not f.is_symlink():self.assertNotIn(self.data['password'],f.read_text(errors='ignore'))
  secret=[c for c in self.calls if c[0][0].endswith('/chpasswd')][0]
  self.assertNotIn(self.data['password'],' '.join(secret[0]));self.assertIn(self.data['password'].encode(),secret[1]['input'])
  with self.assertRaises(ValueError):m.apply(self.data,self.root,self.run_cmd)
 def test_password_failure_rolls_back_new_account(self):
  def fail(args,**kw):
   if args[0].endswith('/chpasswd'):
    self.calls.append((args,kw));raise subprocess.CalledProcessError(1,args)
   return self.run_cmd(args,**kw)
  with self.assertRaisesRegex(ValueError,'设置账户密码'):m.apply(self.data,self.root,fail)
  self.assertFalse((self.root/'var/lib/f8-pro/first-run/complete.json').exists())
  self.assertIn('User=f8setup',(self.root/'etc/sddm.conf.d/99-f8-first-run.conf').read_text())
  self.assertIn(['/usr/sbin/userdel','-r','demo'],[x[0] for x in self.calls])
  self.assertTrue(m.apply(self.data,self.root,self.run_cmd)['ok'])
 def test_existing_account_not_modified(self):
  with self.assertRaises(ValueError):m.apply(dict(self.data,username='root'),self.root,self.run_cmd)
  self.assertEqual(self.calls,[])
 def test_existing_home_preserved(self):
  p=self.root/'home/demo';p.mkdir(parents=True);(p/'important').write_text('keep')
  with self.assertRaisesRegex(ValueError,'家目录已存在'):m.apply(self.data,self.root,self.run_cmd)
  self.assertEqual((p/'important').read_text(),'keep');self.assertEqual(self.calls,[])
if __name__=='__main__':unittest.main()
