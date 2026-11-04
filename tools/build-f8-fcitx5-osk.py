"""Pinned Fcitx5 OSK ARM64 build, isolated from live tablet."""
from pathlib import Path
import os,subprocess,json,shutil,tarfile,hashlib,traceback,time
P=Path(__file__).resolve().parents[1];W=Path('/var/tmp/f8-pro-armbian/fcitx5-osk-r1');W.mkdir(parents=True,exist_ok=True)
ref=(P/'local/fcitx5-osk-source/commit.txt').read_text().strip();src=W/('fcitx5-osk-'+ref)
log=(W/'build.log').open('a',buffering=1)
def state(stage,**kw):(W/'status.json').write_text(json.dumps(dict(stage=stage,time=time.time(),**kw)))
def run(a,**kw):
 log.write('RUN '+repr(a)+'\n');subprocess.run(a,stdout=log,stderr=subprocess.STDOUT,check=True,**kw)
try:
 if not src.exists():
  with tarfile.open(P/'downloads/fcitx5-osk'/(ref+'.tar.gz')) as t:t.extractall(W,filter='data')
 subprocess.run(['python3',str(P/'armbian/fcitx5/patch-osk-haptic.py'),str(src)],check=True)
 base=Path('/var/tmp/f8-pro-phira-arm64');R=base/'sysroot'
 env=dict(os.environ,CARGO_HOME=str(base/'cargo'),RUSTUP_HOME=str(base/'rustup'),CARGO_NET_GIT_FETCH_WITH_CLI='true',GIT_TERMINAL_PROMPT='0',CARGO_BUILD_JOBS='6',CARGO_PROFILE_RELEASE_LTO='false',CARGO_PROFILE_RELEASE_CODEGEN_UNITS='16',CARGO_PROFILE_RELEASE_OPT_LEVEL='2',CARGO_TARGET_AARCH64_UNKNOWN_LINUX_GNU_LINKER='aarch64-linux-gnu-gcc',CC_aarch64_unknown_linux_gnu='aarch64-linux-gnu-gcc',CXX_aarch64_unknown_linux_gnu='aarch64-linux-gnu-g++',PKG_CONFIG_ALLOW_CROSS='1',PKG_CONFIG_SYSROOT_DIR=str(R),PKG_CONFIG_LIBDIR=str(R/'usr/lib/aarch64-linux-gnu/pkgconfig')+':'+str(R/'usr/lib/pkgconfig'))
 env['PATH']=str(base/'cargo/bin')+':'+env['PATH']
 env['CARGO_TARGET_AARCH64_UNKNOWN_LINUX_GNU_RUSTFLAGS']='-L native='+str(R/'usr/lib/aarch64-linux-gnu')+' -C link-arg=-Wl,-rpath-link='+str(R/'usr/lib/aarch64-linux-gnu')
 state('compile',commit=ref)
 run([str(base/'cargo/bin/cargo'),'+nightly-2026-01-01','build','--message-format=short','--release','--locked','--no-default-features','-p','fcitx5-osk','-p','fcitx5-osk-kwin-launcher','-p','fcitx5-osk-key-helper','--target','aarch64-unknown-linux-gnu'],cwd=src,env=env,timeout=1800)
 out=P/'outputs/armbian/f8-fcitx5-r1';out.mkdir(parents=True,exist_ok=True)
 binaries={}
 for name in ['fcitx5-osk','fcitx5-osk-kwin-launcher','fcitx5-osk-key-helper']:
  p=src/'target/aarch64-unknown-linux-gnu/release'/name;shutil.copyfile(p,out/name);binaries[name]=dict(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
 state('built',commit=ref,binaries=binaries)
 (out/'build-manifest.json').write_text((W/'status.json').read_text())
except BaseException as e:
 log.write(traceback.format_exc());state('failed',error=str(e));raise
