"""Compile two KDE plugins using extracted headers; install no build packages."""
import hashlib,json,os,shutil,subprocess,tarfile,time,traceback
from pathlib import Path
W=Path(__file__).resolve().parent;S=W/'ksystemstats-6.6.6';D=W/'deps';log=(W/'build.log').open('a',buffering=1)
def status(stage,**extra):(W/'status.json').write_text(json.dumps({'stage':stage,'time':time.time(),**extra},indent=2)+'\n')
def run(args,**kwargs):
 log.write('RUN '+repr([str(x) for x in args])+'\n');subprocess.run([str(x) for x in args],check=True,stdout=log,stderr=subprocess.STDOUT,**kwargs)
try:
 status('download_headers')
 debs=W/'debs';debs.mkdir(exist_ok=True)
 pkgs=['qt6-base-dev','qt6-base-dev-tools','qt6-declarative-dev','libksysguard-dev','libkf6coreaddons-dev','libkf6i18n-dev','libkf6solid-dev','libkf6kio-dev','libudev-dev','libsensors-dev']
 if len(list(debs.glob('*.deb')))<len(pkgs):run(['apt-get','download',*pkgs],cwd=debs,timeout=240)
 D.mkdir(exist_ok=True)
 for p in debs.glob('*.deb'):run(['dpkg-deb','-x',p,D],timeout=30)
 status('prepare_source')
 if not S.exists():
  with tarfile.open(W/'source.tar.gz') as a:a.extractall(W,filter='data')
 run(['/usr/bin/python3',W/'patch-source.py',S],timeout=10)
 inc=[D/'usr/include',D/'usr/include/aarch64-linux-gnu/qt6',D/'usr/include/KF6',D/'usr/include/ksysguard']
 for parent in [D/'usr/include/aarch64-linux-gnu/qt6',D/'usr/include/KF6']:
  if parent.exists():inc.extend(p for p in parent.iterdir() if p.is_dir())
 for p in D.rglob('SensorPlugin.h'):
  if p.parent.name=='systemstats':inc.append(p.parent.parent)
 flags=['-std=c++20','-O2','-fPIC','-DQT_NO_DEBUG',*[f'-I{p}' for p in inc]]
 mocflags=[f for f in flags if f.startswith(('-I','-D'))]
 moc=D/'usr/lib/qt6/libexec/moc';assert moc.is_file(),list(D.rglob('moc'))
 gpu=S/'plugins/gpu';disk=S/'plugins/disks'
 (gpu/'debug.h').write_text('#pragma once\n#include <QLoggingCategory>\nQ_DECLARE_LOGGING_CATEGORY(KSYSTEMSTATS_GPU)\n')
 (gpu/'debug.cpp').write_text('#include "debug.h"\nQ_LOGGING_CATEGORY(KSYSTEMSTATS_GPU,"org.kde.ksystemstats.gpu")\n')
 (gpu/'IntelHelperLocation.h').write_text('constexpr auto helperLocation = "/usr/lib/aarch64-linux-gnu/libexec/ksystemstats_intel_helper";\n')
 output=W/'output';output.mkdir(exist_ok=True)
 jobs={'gpu':['GpuPlugin','GpuBackend','GpuDevice','AllGpus','LinuxAmdGpu','LinuxIntelGpu','LinuxNvidiaGpu','LinuxBackend','NvidiaGpu','NvidiaSmiProcess','LinuxPanthorGpu','debug'],'disk':['disks']}
 libs=['libQt6Core.so.6','libQt6DBus.so.6','libQt6Network.so.6','libQt6Gui.so.6','libKF6CoreAddons.so.6','libKF6I18n.so.6','libKSysGuardSystemStats.so.2','libudev.so.1','libsensors.so.5']
 for kind,names in jobs.items():
  status('compile_'+kind);src=gpu if kind=='gpu' else disk
  for h in src.glob('*.h'):
   if 'Q_OBJECT' in h.read_text():run([moc,*mocflags,'-I'+str(src),h,'-o',src/('moc_'+h.stem+'.cpp')],timeout=20)
  for name in names:
   cpp=src/(name+'.cpp')
   if '#include "'+name+'.moc"' in cpp.read_text():run([moc,*mocflags,'-I'+str(src),cpp,'-o',src/(name+'.moc')],timeout=20)
  objects=[]
  for name in names:
   obj=src/(name+'.o');run(['g++',*flags,'-I'+str(src),'-c',src/(name+'.cpp'),'-o',obj],timeout=90);objects.append(obj)
  target=output/('ksystemstats_plugin_'+kind+'.so')
  extra=['libKF6KIOCore.so.6','libKF6Solid.so.6'] if kind=='disk' else []
  run(['g++','-shared','-Wl,-z,defs','-o',target,*objects,*['-l:'+x for x in libs+extra]],timeout=30)
  run(['strip','--strip-unneeded',target],timeout=10)
 status('built',plugins={p.name:{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in output.glob('*.so')})
except Exception as e:
 log.write(traceback.format_exc());status('failed',error=str(e),tail=(W/'build.log').read_text()[-7000:]);raise
