from pathlib import Path
import tempfile,importlib.util,json
P=Path(__file__).resolve().parents[1];s=importlib.util.spec_from_file_location('relay_root',P/'tools/install-f8-sensor-relay-root.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
with tempfile.TemporaryDirectory(prefix='f8-relay-root-test-') as tmp:
 R=Path(tmp);(R/'etc').mkdir();(R/'usr/lib').mkdir(parents=True);(R/'lib').symlink_to('usr/lib')
 one=m.install(R);two=m.install(R);assert one['files']==two['files']
 assert not (R/'home').exists()
 assert all((R/k).is_symlink() and (R/k).resolve().exists() for k in m.LINKS)
 print(json.dumps({'files':len(one['files']),'idempotent':True,'user_calibration_copied':False,'links_valid':True}))
