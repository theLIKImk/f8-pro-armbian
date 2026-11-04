#!/usr/bin/python3 -I
"""Full-performance boot path; P2A/P1 rollback boots deliberately skip it."""
import argparse,json,subprocess,sys,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from performance_state import profile,text
a=argparse.ArgumentParser();a.add_argument('stage',choices=['gpu','cpu']);args=a.parse_args()
marker=Path('/proc/device-tree/chosen/f8-gpu-trial')
if not marker.exists() or marker.read_bytes()!=b'p3-1000mhz\0':sys.exit(0)
if args.stage=='gpu':
 p=Path('/sys/class/devfreq/fb000000.gpu-panthor')
 for i in range(40):
  if (p/'available_frequencies').exists():break
  time.sleep(.25)
 allowed=[int(v) for v in text(p/'available_frequencies').split() if int(v)<=profile()['validated_max_mhz']['gpu']*1000000]
 if not allowed:raise RuntimeError('No validated GPU frequency')
 (p/'min_freq').write_text(str(min(allowed)));(p/'max_freq').write_text(str(max(allowed)));(p/'governor').write_text('simple_ondemand')
 print(json.dumps({'gpu_boot_ceiling':max(allowed)}))
else:
 if not list(Path('/sys/devices/system/cpu/cpufreq').glob('policy*')):
  subprocess.run(['/usr/local/lib/f8-pro/performance-apply.py','--enable-cpu'],check=True,timeout=45)
