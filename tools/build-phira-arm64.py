"""Isolated Linux ARM64 cross-build on WSL; no changes to tablet or host packages."""
import argparse,concurrent.futures,hashlib,json,os,shutil,subprocess,tarfile,threading,time,tomllib,traceback,urllib.request
from pathlib import Path
P=Path(__file__).resolve().parents[1];W=Path('/var/tmp/f8-pro-phira-arm64');W.mkdir(exist_ok=True)
S=W/'src';R=W/'sysroot';target='aarch64-unknown-linux-gnu';toolchain='nightly-2026-01-01'
lock=threading.Lock();states={};log=(W/'build.log').open('a',buffering=1)
parser=argparse.ArgumentParser();parser.add_argument('--f8',action='store_true');args=parser.parse_args()
def status(task,stage,**kw):
 with lock:
  states[task]={'stage':stage,'time':time.time(),**kw};(W/'status.json').write_text(json.dumps(states,indent=2)+'\n')
def run(a,**kw):
 with lock:log.write('RUN '+repr([str(x) for x in a])+'\n')
 subprocess.run([str(x) for x in a],check=True,stdout=log,stderr=subprocess.STDOUT,**kw)
def fetch(url,dest):
 if not dest.exists():
  temp=dest.with_suffix(dest.suffix+'.part')
  with urllib.request.urlopen(url,timeout=60) as r,temp.open('wb') as f:shutil.copyfileobj(r,f)
  temp.replace(dest)
 return dest
env=dict(os.environ,CARGO_HOME=str(W/'cargo'),RUSTUP_HOME=str(W/'rustup'),RUSTUP_INIT_SKIP_PATH_CHECK='yes',CARGO_NET_GIT_FETCH_WITH_CLI='true',GIT_TERMINAL_PROMPT='0')
env['PATH']=str(W/'cargo/bin')+':'+env['PATH']
try:
 assert shutil.which('aarch64-linux-gnu-gcc'),'Cross C compiler required'
 if not S.exists():shutil.copytree(P/'games/phira',S,ignore=shutil.ignore_patterns('target','data','cache'))
 if args.f8:
  baseline=S/'target'/target/'release/phira-main'
  if baseline.exists() and not (W/'phira-upstream').exists():shutil.copyfile(baseline,W/'phira-upstream')
  for name in ['Cargo.toml','Cargo.lock','prpr/src/lib.rs','prpr/src/scene.rs','phira/build.rs']:
   shutil.copyfile(P/'games/phira'/name,S/name)
  shutil.copytree(P/'games/phira/vendor/miniquad',S/'vendor/miniquad',dirs_exist_ok=True,ignore=shutil.ignore_patterns('target','.git'))
  shutil.copytree(P/'games/phira/vendor/sasa',S/'vendor/sasa',dirs_exist_ok=True,ignore=shutil.ignore_patterns('target','.git'))
  shutil.copyfile(P/'games/phira/vendor/F8-ORIGINS.md',S/'vendor/F8-ORIGINS.md')
  env['BUILD_ID']='f8-r1'
 def rust():
  status('rust','install_toolchain')
  init=fetch('https://static.rust-lang.org/rustup/dist/x86_64-unknown-linux-gnu/rustup-init',W/'rustup-init');init.chmod(0o755)
  if not (W/'cargo/bin/rustup').exists():run([init,'-y','--no-modify-path','--profile','minimal','--default-toolchain','none'],env=env,timeout=300)
  run([W/'cargo/bin/rustup','toolchain','install',toolchain,'--profile','minimal','--target',target],env=env,timeout=900)
  # The F8 checkout ships the path-patched lockfile; do not update unrelated
  # target dependencies while applying the local Linux integration patches.
  status('rust','fetch_crates')
  run([W/'cargo/bin/cargo','+'+toolchain,'fetch','--locked','--target',target],cwd=S,env=env,timeout=900)
  status('rust','ready')
 def multimedia():
  status('multimedia','prepare_alsa')
  R.mkdir(exist_ok=True)
  for name in ['libasound2','libasound2-dev']:
   f=fetch('https://deb.debian.org/debian/pool/main/a/alsa-lib/'+name+'_1.2.8-1+b1_arm64.deb',W/(name+'.deb'))
   assert subprocess.check_output(['dpkg-deb','-f',f,'Architecture'],text=True).strip()=='arm64'
   run(['dpkg-deb','-x',f,R],timeout=30)
  packages=[('w/wayland',n,'1.21.0-1') for n in ['libwayland-dev','libwayland-client0','libwayland-cursor0','libwayland-egl1','libwayland-server0']]+[('libf/libffi',n,'3.4.4-1') for n in ['libffi8','libffi-dev']]
  for pool,name,version in packages:
   f=fetch('https://deb.debian.org/debian/pool/main/'+pool+'/'+name+'_'+version+'_arm64.deb',W/(name+'.deb'))
   assert subprocess.check_output(['dpkg-deb','-f',f,'Architecture'],text=True).strip()=='arm64'
   run(['dpkg-deb','-x',f,R],timeout=30)
  status('multimedia','build_zlib')
  z=fetch('https://zlib.net/fossils/zlib-1.3.1.tar.gz',W/'zlib-1.3.1.tar.gz')
  if not (W/'zlib-1.3.1').exists():
   with tarfile.open(z) as a:a.extractall(W,filter='data')
  if not (W/'zlib-pic-built').exists():
   ze=dict(env,CC='aarch64-linux-gnu-gcc',AR='aarch64-linux-gnu-ar',RANLIB='aarch64-linux-gnu-ranlib',CFLAGS='-O3 -fPIC')
   if (W/'zlib-1.3.1/Makefile').exists():run(['make','clean'],cwd=W/'zlib-1.3.1',env=ze,timeout=30)
   run(['./configure','--static','--prefix=/usr'],cwd=W/'zlib-1.3.1',env=ze,timeout=60)
   run(['make','-j6'],cwd=W/'zlib-1.3.1',env=ze,timeout=180)
   run(['make','DESTDIR='+str(R),'install'],cwd=W/'zlib-1.3.1',env=ze,timeout=30)
   (W/'zlib-pic-built').write_text('PIC static zlib\n')
  status('multimedia','build_ffmpeg')
  commit='140fd653aed8cad774f991ba083e2d01e86420c7'
  f=fetch('https://codeload.github.com/FFmpeg/FFmpeg/tar.gz/'+commit,W/'ffmpeg-source.tar.gz')
  F=W/('FFmpeg-'+commit)
  if not F.exists():
   with tarfile.open(f) as a:a.extractall(W,filter='data')
  output=W/'static'/target;output.mkdir(parents=True,exist_ok=True)
  version=(S/'prpr-avc/ffmpeg-version').read_text().strip()
  libs=['libavcodec.a','libavformat.a','libavutil.a','libswresample.a','libswscale.a']
  if not all((output/n).exists() for n in libs):
   cfg=tomllib.loads((P/'games/prpr-avc-ffmpeg/config/ffmpeg.toml').read_text())
   run(['./configure',*cfg['configure_common'],'--arch=aarch64','--target-os=linux','--enable-cross-compile','--cross-prefix=aarch64-linux-gnu-','--enable-pic','--prefix='+str(W/'ffmpeg-install')],cwd=F,env=env,timeout=180)
   run(['make','-j6'],cwd=F,env=env,timeout=900);run(['make','install'],cwd=F,env=env,timeout=90)
   for n in libs:shutil.copyfile(W/'ffmpeg-install/lib'/n,output/n)
  (output/'.version').write_text(version+'\n')
  status('multimedia','ready',ffmpeg_commit=commit,libraries={n:hashlib.sha256((output/n).read_bytes()).hexdigest() for n in libs})
 def work(name,fn):
  try:fn()
  except BaseException as e:status(name,'failed',error=str(e));raise
 with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
  jobs=[pool.submit(work,'rust',rust),pool.submit(work,'multimedia',multimedia)]
  for job in jobs:job.result()
 status('game','compile_release')
 assert shutil.which('aarch64-linux-gnu-g++'),'Cross C++ compiler required'
 env.update(CARGO_TARGET_AARCH64_UNKNOWN_LINUX_GNU_LINKER='aarch64-linux-gnu-gcc',CC_aarch64_unknown_linux_gnu='aarch64-linux-gnu-gcc',CXX_aarch64_unknown_linux_gnu='aarch64-linux-gnu-g++',AR_aarch64_unknown_linux_gnu='aarch64-linux-gnu-ar',PKG_CONFIG_ALLOW_CROSS='1',PKG_CONFIG_SYSROOT_DIR=str(R),PKG_CONFIG_LIBDIR=str(R/'usr/lib/aarch64-linux-gnu/pkgconfig')+':'+str(R/'usr/lib/pkgconfig'),PRPR_AVC_LIBS=str(W/'static'),CARGO_BUILD_JOBS='6')
 env['CARGO_TARGET_AARCH64_UNKNOWN_LINUX_GNU_RUSTFLAGS']='-L native='+str(R/'usr/lib')+' -C link-arg=-Wl,-rpath-link='+str(R/'usr/lib/aarch64-linux-gnu')
 run([W/'cargo/bin/cargo','+'+toolchain,'build','--release','--locked','-p','phira-main','--target',target],cwd=S,env=env,timeout=2400)
 binary=S/'target'/target/'release/phira-main';assert binary.exists()
 status('game','built_not_packaged',profile='f8-r1' if args.f8 else 'upstream',binary=str(binary),bytes=binary.stat().st_size,sha256=hashlib.sha256(binary.read_bytes()).hexdigest())
except BaseException as e:
 log.write(traceback.format_exc());status('error','failed',error=str(e),tail=(W/'build.log').read_text()[-7000:]);raise
