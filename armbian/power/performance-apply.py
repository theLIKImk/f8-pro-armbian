#!/usr/bin/python3 -I
"""Authenticated, bounded sysfs frequency changes. No clock/voltage backdoors."""
import argparse,fcntl,hashlib,json,os,subprocess,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from performance_state import DEVICES,snapshot,validate,text,profile

def write_range(p,low,high,gpu):
 lo=p/('min_freq' if gpu else 'scaling_min_freq');hi=p/('max_freq' if gpu else 'scaling_max_freq')
 # Expand first, then narrow: every intermediate min/max pair is valid.
 oldlo,oldhi=int(text(lo)),int(text(hi))
 lo.write_text(str(min(oldlo,low)));hi.write_text(str(max(oldhi,high)))
 lo.write_text(str(low));hi.write_text(str(high))
def apply(requests):
 plans=[validate(snapshot(r['key']),r['mode'],r.get('minimum'),r.get('maximum')) for r in requests]
 before={p['key']:snapshot(p['key']) for p in plans};done=[]
 try:
  for plan in plans:
   key=plan['key'];p=DEVICES[key][1];done.append(key)
   write_range(p,plan['minimum'],plan['maximum'],key=='gpu')
   (p/('governor' if key=='gpu' else 'scaling_governor')).write_text(plan['governor'])
   now=snapshot(key)
   if (now['minimum'],now['maximum'],now['governor'])!=(plan['minimum'],plan['maximum'],plan['governor']):raise RuntimeError('驱动未接受所选配置')
 except Exception:
  for key in reversed(done):
   try:
    p=DEVICES[key][1];s=before[key];write_range(p,s['minimum'],s['maximum'],key=='gpu')
    (p/('governor' if key=='gpu' else 'scaling_governor')).write_text(s['governor'])
   except OSError:pass
  raise
 return {key:snapshot(key) for key in done}
def enable_cpu():
 policies=Path('/sys/devices/system/cpu/cpufreq')
 if list(policies.glob('policy*')):raise ValueError('CPU 调频接口已存在，请直接调整')
 if text('/proc/device-tree/chosen/f8-cpu-trial').strip('\0')!='p2-fixedvolt-1200mhz':raise ValueError('请先启动到 CPU P2A 测试版本')
 if text('/sys/module/cpufreq/parameters/off')!='0':raise ValueError('当前启动未开放 CPU 调频')
 version=profile().get('cpu_module_version','p2')
 if version not in {'p2','p3'}:raise ValueError('不支持的 CPU 模块版本')
 p=Path('/usr/local/lib/f8-pro/experimental/f8-cpufreq-'+version+'.ko');st=p.stat()
 if p.is_symlink() or st.st_uid!=0 or st.st_mode&0o022 or hashlib.sha256(p.read_bytes()).hexdigest()!=profile()['cpu_module_sha256']:raise ValueError('CPU 模块校验未通过')
 args=['max_little_khz=1800000','max_big_khz=2400000'] if version=='p3' else []
 subprocess.run(['/usr/sbin/insmod',str(p),*args],check=True,capture_output=True,timeout=30)
 if not all(snapshot(k)['enabled'] for k in ['cpu0','cpu4','cpu6']):
  subprocess.run(['/usr/sbin/rmmod','f8_cpufreq_'+version],capture_output=True,timeout=15)
  raise ValueError('CPU 接口不完整，已尝试退出测试驱动')
 return apply([{'key':k,'mode':'auto'} for k in ['cpu0','cpu4','cpu6']])
def main():
 if os.geteuid()!=0:raise PermissionError('需要管理员验证')
 if b'rockchip,rk3588s-tablet-f12-v11\0' not in Path('/proc/device-tree/compatible').read_bytes():raise ValueError('不支持的设备')
 a=argparse.ArgumentParser();a.add_argument('--device',choices=list(DEVICES));a.add_argument('--mode',choices=['auto','fixed','range']);a.add_argument('--minimum',type=int);a.add_argument('--maximum',type=int);group=a.add_mutually_exclusive_group();group.add_argument('--all-auto',action='store_true');group.add_argument('--enable-cpu',action='store_true');args=a.parse_args()
 if args.enable_cpu:
  if any(v is not None for v in [args.device,args.mode,args.minimum,args.maximum]):raise ValueError('参数冲突')
  requests=None
 elif args.all_auto:
  if any(v is not None for v in [args.device,args.mode,args.minimum,args.maximum]):raise ValueError('参数冲突')
  requests=[{'key':key,'mode':'auto'} for key in DEVICES if snapshot(key)['enabled']]
 else:
  if not args.device or not args.mode:raise ValueError('需要选择设备及模式')
  requests=[{'key':args.device,'mode':args.mode,'minimum':args.minimum,'maximum':args.maximum}]
 lock=os.open('/run/lock/f8-performance.lock',os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW,0o600)
 with os.fdopen(lock,'w') as f:
  fcntl.flock(f,fcntl.LOCK_EX);result=enable_cpu() if args.enable_cpu else apply(requests)
 print(json.dumps({'ok':True,'devices':result},ensure_ascii=False))
if __name__=='__main__':
 try:main()
 except Exception as e:print(json.dumps({'ok':False,'error':str(e)},ensure_ascii=False));sys.exit(1)
