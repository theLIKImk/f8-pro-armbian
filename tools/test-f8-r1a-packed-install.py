"""Run the actual packed install patch in an isolated ARM64 BusyBox chroot."""
from pathlib import Path
import gzip,hashlib,importlib.util,json,os,shutil,subprocess,sys
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'tools'))
from inspect_images import fdt
O=P/'outputs/armbian/f8-first-run-r1a';m=json.loads((O/'preflight.json').read_text())
blob=(O/m['file']).read_bytes();assert hashlib.sha256(blob).hexdigest()==m['sha256']
t=fdt(blob);q=t['/images/ramdisk'];a=int.from_bytes(q['data-position'],'big');n=int.from_bytes(q['data-size'],'big')
s=importlib.util.spec_from_file_location('cpio',P/'tools/build-usb-bootlog.py');c=importlib.util.module_from_spec(s);s.loader.exec_module(c)
files={name:b for name,v,b in c.cpio_read(gzip.decompress(blob[a:a+n]))}
patch=(O/'patch-init.sh').read_bytes();assert files['init'].count(patch)==1
R=Path('/var/tmp/f8-pro-armbian/first-run-r1a/install-fixture');assert not R.exists();R.mkdir()
for name in ['bin','mnt/root/usr/local/lib/f8-pro','mnt/root/etc/systemd/system']:(R/name).mkdir(parents=True,exist_ok=True)
busy=R/'bin/busybox';busy.write_bytes(files['bin/busybox']);busy.chmod(0o755)
for name in ['sha256sum','mkdir','cp','chmod','chown','mv','ln','readlink']:(R/'bin'/name).symlink_to('busybox')
for name in m['assets']:
 assert hashlib.sha256(files[name]).hexdigest()==m['assets'][name];(R/name).write_bytes(files[name])
marker=R/'mnt/root/etc/f8-pro-release-r1';marker.touch()
helper=R/'mnt/root/usr/local/lib/f8-pro/first-run-apply.py'
old=Path('/var/tmp/f8-pro-armbian/release-r1/first-run-apply-before-r1a.py').read_bytes();assert hashlib.sha256(old).hexdigest()==m['helper_before_sha256'];helper.write_bytes(old)
(R/'patch.sh').write_bytes(b'#!/bin/sh\nset -eu\nPATH=/bin\nexport PATH\nfail() { echo "$*" >&2; exit 10; }\n'+patch)
def run():return subprocess.run(['chroot',str(R),'/bin/busybox','sh','/patch.sh'],capture_output=True,text=True,timeout=30)
r=run();assert r.returncode==0,r.stderr
assert hashlib.sha256(helper.read_bytes()).hexdigest()==m['helper_after_sha256']
link=R/'mnt/root/etc/systemd/system/f8-desktop.target.wants/f8-root-grow-r1a.service';assert os.readlink(link)=='../f8-root-grow-r1a.service'
assert (R/'mnt/root/var/lib/f8-pro/first-run/helper-before-r1a.py').read_bytes()==old
r=run();assert r.returncode==0,r.stderr
helper.write_bytes(b'other-version\n');r=run();assert r.returncode==10 and 'unexpected-hash' in r.stderr;assert helper.read_bytes()==b'other-version\n'
marker.unlink();r=run();assert r.returncode==0;assert helper.read_bytes()==b'other-version\n'
record={'packed_arm64_patch_executed':True,'initial_install_passed':True,'repeat_install_passed':True,'unexpected_helper_refused':True,'non_r1_root_untouched':True,'grow_service_symlink_correct':True,'growth_not_executed_in_fixture':True,'device_modified':False}
(O/'packed-install-test.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record,indent=2))
