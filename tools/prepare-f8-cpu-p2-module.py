"""Stage only; deliberately do not load or enable the experimental driver."""
import base64,json
from pathlib import Path
P=Path(__file__).resolve().parents[1];O=P/'outputs/armbian/f8-cpu-p2a'
meta=json.loads((O/'module-check.json').read_text());assert meta['actual_image_import_crcs_verified']
data=base64.b64encode((O/'f8-cpufreq-p2.ko').read_bytes()).decode()
code='''import base64,hashlib,json,os,subprocess
from pathlib import Path
assert os.geteuid()==0 and os.environ.get('SUDO_USER')=='likimk'
assert subprocess.check_output(['uname','-r'],text=True).strip()=='6.1.115-vendor-rk35xx'
assert not Path('/sys/module/f8_cpufreq_p2').exists()
b=base64.b64decode(DATA);assert hashlib.sha256(b).hexdigest()==DIGEST
p=Path('/usr/local/lib/f8-pro/experimental/f8-cpufreq-p2.ko');p.parent.mkdir(exist_ok=True)
if p.exists():assert p.is_file() and not p.is_symlink() and hashlib.sha256(p.read_bytes()).hexdigest()==DIGEST
p.write_bytes(b);p.chmod(0o644);os.chown(p,0,0)
print(json.dumps({'staged_file':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'loaded':False,'autoload_installed':False},indent=2))
'''.replace('DATA',repr(data)).replace('DIGEST',repr(meta['module_sha256']))
(P/'local/hardware/cpu-p2-module-stage-runner.py').write_text(code)
