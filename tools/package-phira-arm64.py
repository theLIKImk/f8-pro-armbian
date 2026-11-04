"""Package the completed AArch64 build and assets from the matching official release."""
import argparse,hashlib,json,os,shutil,struct,subprocess,tarfile,zipfile
from pathlib import Path,PurePosixPath
P=Path(__file__).resolve().parents[1];W=Path('/var/tmp/f8-pro-phira-arm64')
parser=argparse.ArgumentParser();parser.add_argument('--f8',action='store_true');args=parser.parse_args()
name='Phira-linux-arm64-v0.8.2'+('-f8-r1' if args.f8 else '');O=P/'outputs/games';O.mkdir(parents=True,exist_ok=True)
stage=W/name;assert not stage.exists(),'Preserve previously prepared package'
stage.mkdir();source=W/'src';binary=source/'target/aarch64-unknown-linux-gnu/release/phira-main'
elf=binary.read_bytes();assert elf[:6]==b'\x7fELF\x02\x01' and struct.unpack_from('<H',elf,18)[0]==183
if not args.f8:subprocess.run(['git','diff','--exit-code'],cwd=source,check=True,stdout=subprocess.DEVNULL)
else:
 state=json.loads((W/'status.json').read_text())['game'];assert state['stage']=='built_not_packaged' and state['profile']=='f8-r1'
 assert hashlib.sha256(elf).hexdigest()==state['sha256']
commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=source,text=True).strip();assert commit=='750579396cbc5dc61e6379fbfb2aa1adb70751a6'
shutil.copyfile(binary,stage/'phira');(stage/'phira').chmod(0o755)
shutil.copytree(source/'assets',stage/'assets')
archive=P/'local/phira-build/Phira-linux-x86_64-v0.8.2.zip';added=[]
with zipfile.ZipFile(archive) as z:
 for entry in z.infolist():
  n=PurePosixPath(entry.filename)
  assert not n.is_absolute() and '..' not in n.parts
  if n.parts and n.parts[0]=='assets' and not entry.is_dir():
   dest=stage.joinpath(*n.parts)
   if not dest.exists():dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(z.read(entry));added.append(str(n))
for f in ['font.ttf','background.jpg']:assert (stage/'assets'/f).is_file()
shutil.copyfile(source/'LICENSE',stage/'LICENSE')
shutil.copyfile(W/'FFmpeg-140fd653aed8cad774f991ba083e2d01e86420c7/COPYING.LGPLv2.1',stage/'FFmpeg-COPYING.LGPLv2.1')
(stage/'run-phira.sh').write_text('#!/bin/sh\nset -eu\nappdir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)\ncd "$appdir"\nexec "$appdir/phira" "$@"\n');(stage/'run-phira.sh').chmod(0o755)
if args.f8:
 for n in ['run-phira.sh','alsa-pulse.conf']:shutil.copyfile(P/'armbian/phira'/n,stage/n)
 (stage/'run-phira.sh').chmod(0o755)
 patches=stage/'f8-source';patches.mkdir()
 (patches/'changes.patch').write_bytes(subprocess.check_output(['git','diff','--binary'],cwd=source))
 shutil.copytree(source/'vendor',patches/'vendor',ignore=shutil.ignore_patterns('target','.git','.cargo-ok'))
installer='''#!/usr/bin/python3
from pathlib import Path
p=Path(__file__).resolve().parent
def quoted(s):
 return '"'+str(s).replace('\\\\','\\\\\\\\').replace('"','\\\\"').replace('`','\\\\`').replace('$','\\\\$')+'"'
dest=Path.home()/'.local/share/applications/f8-phira-arm64.desktop'
dest.parent.mkdir(parents=True,exist_ok=True)
text='[Desktop Entry]\\nType=Application\\nName=Phira ARM64\\nName[zh_CN]=Phira ARM64\\nComment=Phira 0.8.2 for Linux ARM64\\nExec='+quoted(p/'run-phira.sh')+'\\nIcon='+str(p/'assets/icon.png')+'\\nTerminal=false\\nCategories=Game;\\n'
if dest.exists() and 'Phira ARM64' not in dest.read_text():raise SystemExit('Existing unrelated launcher preserved')
dest.write_text(text);dest.chmod(0o644);print(dest)
'''
# Keep generated Python syntax checked before shipping.
compile(installer,'install-desktop.py','exec');(stage/'install-desktop.py').write_text(installer);(stage/'install-desktop.py').chmod(0o755)
dynamic=subprocess.check_output(['aarch64-linux-gnu-readelf','-d',binary],text=True)
assert '(RPATH)' not in dynamic and '(RUNPATH)' not in dynamic,'Do not ship WSL build paths in runtime search paths'
(stage/'ELF-DEPENDENCIES.txt').write_text(dynamic)
manifest={'name':'Phira','version':'0.8.2','target':'aarch64-unknown-linux-gnu','source':'https://github.com/TeamFlos/phira','commit':commit,'source_modified':False,'rust_toolchain':'nightly-2026-01-01','video_enabled':True,'ffmpeg_commit':'140fd653aed8cad774f991ba083e2d01e86420c7','ffmpeg_recipe_commit':'1c7bdd1e29291c1cbf336b0323b0774cec21da7c','binary_sha256':hashlib.sha256(elf).hexdigest(),'binary_bytes':len(elf),'assets_supplemented_from_official_release':added,'official_release_archive_sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'tablet_startup_test':'pending'}
(stage/'BUILD-MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
if args.f8:
 manifest.update(source_modified=True,build_id='f8-r1',touch_backend='XInput2 via XWayland',linux_default_sample_rate=48000,text_input='upstream inputbox with Zenity')
 (stage/'BUILD-MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
(stage/'README.txt').write_text('Phira 0.8.2 - Linux ARM64 / AArch64\n\nRun: ./run-phira.sh\nMenu entry: python3 ./install-desktop.py\nExtract into a writable user directory. Game data and cache are stored beside the program.\nThe upstream Linux window backend defaults to X11; KDE Wayland runs it through XWayland.\nVideo decoding is included. No ARM Android APK is included.\n\nSource: https://github.com/TeamFlos/phira/tree/'+commit+'\nBuild recipe: tools/build-phira-arm64.py in the F8 project.\nFFmpeg recipe: https://github.com/TeamFlos/prpr-avc-ffmpeg/tree/1c7bdd1e29291c1cbf336b0323b0774cec21da7c\nFFmpeg source: https://github.com/FFmpeg/FFmpeg/tree/140fd653aed8cad774f991ba083e2d01e86420c7\n')
shutil.copyfile(P/'tools/build-phira-arm64.py',stage/'build-phira-arm64.py')
if args.f8:
 with (stage/'README.txt').open('a') as f:f.write('\nF8 R1: XI2 touchscreen input; upstream Zenity text dialog; 48 kHz default audio.\nAdditional runtime dependencies: zenity, ALSA Pulse plugin.\nBuild with tools/build-phira-arm64.py --f8 in the F8 project checkout. Local changes and vendored sources are in f8-source.\nNo user data, credentials or game account configuration is included.\n')
dest=O/(name+'.tar.gz');assert not dest.exists()
def mode(info):
 info.uid=info.gid=0;info.uname=info.gname='root';info.mode=0o755 if info.isdir() or info.name.endswith(('/phira','/run-phira.sh','/install-desktop.py')) else 0o644
 return info
with tarfile.open(dest,'w:gz') as t:t.add(stage,arcname=name,filter=mode)
digest=hashlib.sha256(dest.read_bytes()).hexdigest();(O/(name+'.sha256')).write_text(digest+'  '+dest.name+'\n')
(O/(name+'-build.json')).write_text(json.dumps({**manifest,'package_sha256':digest,'package_bytes':dest.stat().st_size},indent=2)+'\n')
print(json.dumps({'package':str(dest),'bytes':dest.stat().st_size,'sha256':digest,'binary_sha256':manifest['binary_sha256'],'extra_assets':added},indent=2))
