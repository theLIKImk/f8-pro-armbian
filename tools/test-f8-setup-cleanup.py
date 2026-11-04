from pathlib import Path
import importlib.util,unittest,tempfile,subprocess
P=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('cleanup',P/'armbian/first-run/setup-cleanup.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class Test(unittest.TestCase):
 def state(self):return dict(complete=True,new_user_valid=True,new_wayland_active=True,setup_exists=True,setup_identity_valid=True,setup_disabled=True,setup_processes=[])
 def test_only_after_valid_new_login_and_no_old_processes(self):
  self.assertEqual(m.decision(self.state()),'retire')
  for key,value in [('complete',False),('new_user_valid',False),('new_wayland_active',False),('setup_processes',[999])]:
   with self.subTest(key=key):self.assertTrue(m.decision(dict(self.state(),**{key:value})).startswith('pending-'))
 def test_unknown_identity_and_enabled_setup_refused(self):
  for key in ['setup_identity_valid','setup_disabled']:
   with self.subTest(key=key):
    with self.assertRaises(ValueError):m.decision(dict(self.state(),**{key:False}))
 def test_idempotent_after_retirement(self):self.assertEqual(m.decision(dict(self.state(),setup_exists=False)),'already-retired')
 def fixture(self,r):
  home=r/'home/f8setup';home.mkdir(parents=True);(home/'saved-file').write_text('keep me')
  sudo=r/'etc/sudoers.d/f8-first-run';sudo.parent.mkdir(parents=True);sudo.write_text('f8setup ALL=(root) NOPASSWD: /usr/local/lib/f8-pro/first-run-apply.py ""\n')
  return home,sudo
 def test_archive_preserves_files_and_userdel_has_no_recursive_flag(self):
  with tempfile.TemporaryDirectory() as td:
   r=Path(td);home,sudo=self.fixture(r);calls=[]
   def run(args,**kw):calls.append(args);return subprocess.CompletedProcess(args,0)
   result=m.retire(r,'newuser',run)
   self.assertEqual(calls,[['/usr/sbin/userdel','f8setup']]);self.assertFalse(home.exists());self.assertFalse(sudo.exists())
   self.assertEqual((Path(result['home_preserved_at'])/'saved-file').read_text(),'keep me')
 def test_failed_userdel_restores_home(self):
  with tempfile.TemporaryDirectory() as td:
   r=Path(td);home,sudo=self.fixture(r)
   def fail(args,**kw):raise subprocess.CalledProcessError(8,args)
   with self.assertRaises(ValueError):m.retire(r,'newuser',fail)
   self.assertEqual((home/'saved-file').read_text(),'keep me');self.assertTrue(sudo.exists())
if __name__=='__main__':unittest.main()
