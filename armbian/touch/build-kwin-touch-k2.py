"""Build matching Ubuntu KWin in isolation. Never install packages or replace KWin."""
import apt,concurrent.futures,hashlib,json,os,re,subprocess,tarfile,time,traceback,urllib.request
from pathlib import Path
W=Path(__file__).resolve().parent;D=W/'deps';B=W/'build';S=W/'kwin-6.6.6'
log=(W/'build.log').open('a',buffering=1)
def status(stage,**kw):(W/'status.json').write_text(json.dumps({'stage':stage,'time':time.time(),**kw},indent=2)+'\n')
def run(a,**kw):
 log.write('RUN '+repr([str(x) for x in a])+'\n');subprocess.run([str(x) for x in a],stdout=log,stderr=subprocess.STDOUT,check=True,**kw)
try:
 status('resolve_headers_without_installing')
 cache=apt.Cache();names=json.loads((W/'build-packages.json').read_text())
 selected={};seen=set();queue=list(names)+['cmake','pkgconf','patch']
 while queue:
  name=queue.pop()
  if name in seen:continue
  seen.add(name)
  assert name in cache and cache[name].candidate is not None,name
  p=cache[name];v=p.candidate
  # Installed runtime dependencies stay on the running system. Development
  # files and missing build tools are extracted, never installed by apt.
  if p.is_installed and name not in names and not name.endswith(('-dev','-dev-tools','-private-dev')) and name not in ['cmake','pkgconf','patch']:continue
  selected[name]=v.version
  for group in v.dependencies:
   if group.rawtype not in ['Depends','PreDepends']:continue
   choices=[x.name for x in group.or_dependencies if x.name in cache and cache[x.name].candidate is not None]
   if not choices:
    choices=list(dict.fromkeys(p.name for x in group.or_dependencies for p in cache.get_providing_packages(x.name) if p.candidate is not None))
   assert choices,(name,str(group))
   queue.append(next((n for n in choices if cache[n].is_installed),choices[0]))
 # Qt private headers must match the live runtime, not just meet a minimum.
 for dev,runtime in [('qt6-base-dev','libqt6core6t64'),('qt6-declarative-dev','libqt6qml6')]:
  assert cache[runtime].is_installed and cache[dev].candidate.version==cache[runtime].installed.version,(dev,cache[dev].candidate.version,cache[runtime].installed.version if cache[runtime].is_installed else None)
 (W/'resolved-packages.json').write_text(json.dumps(selected,indent=2)+'\n')
 debs=W/'debs';debs.mkdir(exist_ok=True);D.mkdir(exist_ok=True)
 status('download_headers',count=len(selected))
 def fetch(item):
  name,version=item;v=cache[name].candidate;assert v.version==version
  uri=v.uri.replace('http://ports.ubuntu.com/','https://ports.ubuntu.com/')
  filename=Path(v.filename).name;assert filename.endswith('.deb')
  sha=v.record['SHA256'];dest=debs/filename
  if dest.exists() and hashlib.sha256(dest.read_bytes()).hexdigest()==sha:return name
  temp=debs/(filename+'.f8part')
  for attempt in range(3):
   try:
    with urllib.request.urlopen(uri,timeout=25) as r,temp.open('wb') as f:
     while chunk:=r.read(256*1024):f.write(chunk)
    assert hashlib.sha256(temp.read_bytes()).hexdigest()==sha,(name,'package SHA256 mismatch')
    temp.replace(dest);return name
   except Exception:
    if attempt==2:raise
 with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
  futures=[pool.submit(fetch,item) for item in sorted(selected.items())]
  for i,f in enumerate(concurrent.futures.as_completed(futures),1):
   name=f.result();log.write('FETCHED '+name+'\n');status('download_headers',count=len(selected),completed=i,last=name)
 status('extract_headers',count=len(selected))
 # Old apt attempts may leave an epoch-escaped, truncated .deb beside the
 # SHA-verified downloads. Extract only the explicitly selected artifacts.
 if not (W/'deps-extracted').exists():
  for name in sorted(selected):
   v=cache[name].candidate;f=debs/Path(v.filename).name
   assert hashlib.sha256(f.read_bytes()).hexdigest()==v.record['SHA256'],name
   run(['dpkg-deb','-x',f,D],timeout=45)
  (W/'deps-extracted').write_text('verified packages extracted before runtime links\n')
 # Fill missing runtime import targets with links to existing system files;
 # never traverse an existing destination link or write through it.
 def mirror(src,dest):
  if dest.is_symlink():return
  dest.mkdir(parents=True,exist_ok=True)
  for p in src.iterdir():
   q=dest/p.name
   if q.is_symlink():continue
   if not q.exists():q.symlink_to(p,target_is_directory=p.is_dir())
   elif q.is_dir() and p.is_dir():mirror(p,q)
 for p in ['/usr/lib/aarch64-linux-gnu','/usr/lib/qt6','/usr/include']:
  if Path(p).exists():mirror(Path(p),D/p.lstrip('/'))
 status('source')
 artifacts={'kwin_6.6.6.orig.tar.xz':'76314bb5053943003c089bd8997b159c70a8bc35ba87dc3a10885ade8f561953','kwin_6.6.6-0ubuntu0.1.debian.tar.xz':'f8e51babdd9fd39760cb207877f0f9f8f2efec09202aeb926498d981e4c7263c'}
 for name,sha in artifacts.items():
  p=W/name
  if not p.exists():p.write_bytes(urllib.request.urlopen('https://ports.ubuntu.com/pool/universe/k/kwin/'+name,timeout=90).read())
  assert hashlib.sha256(p.read_bytes()).hexdigest()==sha,name
 if not S.exists():
  with tarfile.open(W/'kwin_6.6.6.orig.tar.xz') as t:t.extractall(W,filter='data')
 if not (S/'debian').exists():
  with tarfile.open(W/'kwin_6.6.6-0ubuntu0.1.debian.tar.xz') as t:t.extractall(S,filter='data')
 if not (W/'ubuntu-patches-applied').exists():
  for name in (S/'debian/patches/series').read_text().splitlines():
   if name.strip() and not name.startswith('#'):run([D/'usr/bin/patch','-p1','-i',S/'debian/patches'/name.strip()],cwd=S,timeout=15)
  (W/'ubuntu-patches-applied').write_text('applied\n')
 p=S/'src/input.cpp';src=p.read_text();anchor='    bool touchDown(TouchDownEvent *event) override\n    {\n        if (m_gestureTaken) {'
 replacement='''    bool touchDown(TouchDownEvent *event) override
    {
        // F8 application-first multitouch: retain keyboard/touchpad shortcuts.
        if (!kwinApp()->config()->group(QStringLiteral("Touchscreen")).readEntry("GlobalSwipeGestures", true)) {
            return false;
        }
        if (m_gestureTaken) {'''
 if 'F8 application-first multitouch' not in src:
  assert src.count(anchor)==1
  src=src.replace(anchor,replacement)
  if '#include <KConfigGroup>' not in src:src=src.replace('#include <KLocalizedString>','#include <KLocalizedString>\n#include <KConfigGroup>')
  p.write_text(src)
 env=dict(os.environ);env['PATH']=str(D/'usr/bin')+':'+env['PATH']
 env['LD_LIBRARY_PATH']=str(D/'usr/lib/aarch64-linux-gnu')+':'+str(D/'usr/lib')
 env['PKG_CONFIG_PATH']=':'.join(str(D/x) for x in ['usr/lib/aarch64-linux-gnu/pkgconfig','usr/lib/pkgconfig','usr/share/pkgconfig'])
 env['PKG_CONFIG_SYSROOT_DIR']=str(D)
 status('configure')
 run([D/'usr/bin/cmake','-S',S,'-B',B,'-DCMAKE_BUILD_TYPE=Release','-DBUILD_TESTING=OFF','-DKWIN_BUILD_KCMS=OFF','-DCMAKE_AUTOGEN_PARALLEL=2','-DCMAKE_PREFIX_PATH='+str(D/'usr'),'-DQTWAYLANDSCANNER_KDE_EXECUTABLE='+str(D/'usr/lib/qt6/libexec/qtwaylandscanner')],env=env,timeout=180)
 status('compile')
 run([D/'usr/bin/cmake','--build',B,'--target','kwin','-j3'],env=env,timeout=2400)
 libs=[p for p in B.rglob('libkwin.so.6.6.6') if p.is_file() and not p.is_symlink()];assert len(libs)==1,libs
 status('built_not_installed',library=str(libs[0]),bytes=libs[0].stat().st_size,sha256=hashlib.sha256(libs[0].read_bytes()).hexdigest())
except BaseException as e:
 log.write(traceback.format_exc());status('failed',error=str(e),tail=(W/'build.log').read_text()[-7000:]);raise
