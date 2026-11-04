import json,os,subprocess
from pathlib import Path
assert os.geteuid()==0 and os.environ.get('SUDO_USER')=='likimk'
assert Path('/proc/device-tree/chosen/f8-gpu-trial').read_bytes()==b'p3-1000mhz\0'
assert json.loads(Path('/etc/f8-pro/performance-limits.json').read_text())['validated_max_mhz']['gpu']==1000
old=Path('/proc/sys/kernel/random/boot_id').read_text().strip()
r=subprocess.run(['systemd-run','--quiet','--unit=f8-performance-reboot-check','--on-active=3s','/usr/bin/systemctl','reboot'],check=True,capture_output=True,text=True,timeout=8)
print(json.dumps({'old_boot_id':old,'reboot_scheduled_seconds':3,'exit':r.returncode}))
