from pathlib import Path
import hashlib,json,subprocess,sys,tarfile
p=Path('/mnt/d/Netdisk/Other/F8-PRO/archlinux')
sys.path.insert(0,str(p/'tools'))
import importlib.util
spec=importlib.util.spec_from_file_location('activities',p/'tools/build-plasma-activities.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
name='plasma-activities-6.7.5-1.1-aarch64.pkg.tar.xz';expected='52af4634ba9f567b21a6b805cd9c90168d181cc4cb26aa376b848a11709d14eb'
remote='/home/alarm/f8-pro-builds/plasma-activities-6.7.5-Cl4QcUFV'
out=p/'outputs/plasma-6.7.5';out.mkdir(parents=True,exist_ok=True)
subprocess.run(['scp',*m.OPTIONS,m.HOST+':'+remote+'/'+name,str(out/name)],check=True,timeout=90)
assert hashlib.sha256((out/name).read_bytes()).hexdigest()==expected
elf=[]
with tarfile.open(out/name) as t:
 info=t.extractfile('.PKGINFO').read().decode();buildinfo=t.extractfile('.BUILDINFO').read().decode()
 assert '\narch = aarch64\n' in info and '\npkgver = 6.7.5-1.1\n' in info
 for e in t.getmembers():
  if e.isfile():
   f=t.extractfile(e);h=f.read(20)
   if h[:4]==b'\x7fELF':
    assert h[4:6]==bytes([2,1]) and int.from_bytes(h[18:20],'little')==183
    elf.append(e.name)
assert len(elf)>=3
r={'remote_build_directory':remote,'exit_code':0,'arm64_package_built':True,'package_installed':False,'package':name,'package_sha256':expected,'size_bytes':(out/name).stat().st_size,'elf_architecture_checked':elf,'source_primary_signer':m.SIGNER,'notes':'Native build succeeded; collector initially assumed zst but target makepkg uses xz. Existing artifact collected without rebuild.'}
report=p/'analysis/plasma-6.7.5'
(report/'plasma-activities-native-build.json').write_text(json.dumps(r,indent=2)+'\n')
(report/'plasma-activities-PKGINFO.txt').write_text(info);(report/'plasma-activities-BUILDINFO.txt').write_text(buildinfo)
f=p/'packaging/plasma-6.7.5/plasma-activities/origin.json';o=json.loads(f.read_text());o['built']=True;o['package_sha256']=expected;f.write_text(json.dumps(o,indent=2)+'\n')
print('Package hash, metadata, and '+str(len(elf))+' AArch64 ELF files verified. Bytes='+str((out/name).stat().st_size))
