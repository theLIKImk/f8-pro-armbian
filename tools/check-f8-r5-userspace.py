"""Validate R5 packed helpers, units and handoff rollback without a real boot."""
import gzip
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess

P=Path(__file__).resolve().parents[1]
out=P/'outputs/armbian/firstboot-diagnostic-r5'
work=Path('/var/tmp/f8-pro-armbian/firstboot-diagnostic-r5')
spec=importlib.util.spec_from_file_location('usb_builder',P/'tools/build-usb-bootlog.py')
helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
archive=out/'initramfs-diagnostic.cpio.gz'
records=helper.cpio_read(gzip.decompress(archive.read_bytes()))
contents={name:body for name,_,body in records}
init=contents['init'].decode()
report_script=contents['f8-evaluation-report'].decode()
assert init==(P/'armbian/initramfs/fifthboot-evaluation-init.sh').read_text()
assert report_script==(P/'armbian/initramfs/fifthboot-evaluation-report.sh').read_text()
assert 'mount -t ext4 -o ro,noload /dev/mmcblk0p6 /run/f8/container' in init
assert 'upperdir=/run/f8-overlay/upper,workdir=/run/f8-overlay/work' in init
assert '--unit=f8-evaluation.target' in init and 'sha256sum -c -' in init
assert 'systemd.gpt_auto=0' in init and '[ -s /run/f8/lower/usr/lib/modules/6.1.172-f8-pro-armbian-eval/modules.dep ]' in init
assert 'image=/run/f8/eval-logs.img' in report_script and 'lun.0/ro' in report_script
runtime=work/'dynamic-runtime-check';runtime.mkdir(exist_ok=True)
for name,fields,body in records:
    if name in ['lib','lib64','sbin'] or name.startswith(('lib/','lib64/','sbin/')):
        path=runtime/name
        if stat.S_ISDIR(fields[1]):path.mkdir(parents=True,exist_ok=True)
        else:
            assert stat.S_ISREG(fields[1]);path.parent.mkdir(parents=True,exist_ok=True)
            path.write_bytes(body);path.chmod(fields[1]&0o777)
version=subprocess.check_output(['qemu-aarch64-static','-L',str(runtime),str(runtime/'sbin/blkid'),'--version'],text=True)
assert version.startswith('blkid ')
# Verify actual target dependency graph in a separate hardlink clone. Only ADD
# new unit files; never edit an existing hardlinked file from the frozen root.
root=Path('/var/tmp/f8-pro-armbian/rootfs-trixie-wayland')
check=work/'unit-check-root'
if not check.exists():
    subprocess.run(['cp','-al',str(root),str(check)],check=True)
unit_names=[]
for name,body in contents.items():
    if name.startswith('f8-eval-units/'):
        destination=check/'etc/systemd/system'/Path(name).name
        if destination.exists():assert destination.read_bytes()==body
        else:
            destination.parent.mkdir(parents=True,exist_ok=True)
            with destination.open('xb') as stream:stream.write(body)
        unit_names.append(destination.name)
result=subprocess.run(['systemd-analyze','--root='+str(check),'--man=no','verify',*unit_names],capture_output=True,text=True)
(out/'unit-verification.log').write_text(result.stdout+result.stderr)
assert result.returncode==0,result.stdout+result.stderr
segment=init[init.index('moved=\n'):init.index('\ncd /mnt/root')]
fixtures=[]
for failing in range(5):
    fixture='''
loc_dev=init; loc_proc=init; loc_sys=init; loc_run=init; forward=0
mkdir() { return 0; }
mount() {
    [ "$1" = --move ] || exit 93
    case "$2" in
        /mnt/root/*) name=${2##*/}; eval "current=\\$loc_$name"; [ "$current" = root ] || exit 94; eval "loc_$name=init";;
        /*) name=${2##*/}; forward=$((forward+1)); [ "$forward" != FAIL_AT ] || return 1
            eval "current=\\$loc_$name"; [ "$current" = init ] || exit 95; eval "loc_$name=root";;
        *) exit 96;;
    esac
}
state() { printf '%s %s %s %s\\n' "$loc_dev" "$loc_proc" "$loc_sys" "$loc_run"; }
fail() { state; exit 77; }
'''.replace('FAIL_AT',str(failing))+'\n'+segment+'\nstate\n'
    path=work/('move-fixture-'+str(failing)+'.sh');path.write_text(fixture)
    result=subprocess.run(['qemu-aarch64-static',str(work/'busybox'),'sh',str(path)],capture_output=True,text=True)
    assert result.returncode==(0 if failing==0 else 77),(failing,result.stdout,result.stderr)
    assert result.stdout.strip()==('root root root root' if failing==0 else 'init init init init'),result.stdout
    fixtures.append({'failing_move_index':failing,'passed':True})
# Real non-root traversal fixture: reproduce the 0700 upper metadata policy,
# then check the corrected mode. This does not mount or boot an overlay.
assert 'chmod 0755 /run/f8-overlay/upper || fail upper-mode' in init
assert 'chmod 0644 /mnt/root/etc/systemd/system/f8-evaluation*' in init
assert 'chmod 0644 /mnt/root/usr/lib/systemd/system/f8-pro-ssh-hostkeys.service' in init
fixture=work/'root-mode-fixture'
fixture.mkdir(exist_ok=True)
fixture.chmod(0o755)
fixture_root=fixture/'root';fixture_root.mkdir(exist_ok=True)
(fixture_root/'os-release').write_text('ID=debian\n')
(fixture_root/'os-release').chmod(0o644)
def nobody():
    os.setgroups([])
    os.setgid(65534)
    os.setuid(65534)
def can_read():
    return subprocess.run(['/usr/bin/test','-r',str(fixture_root/'os-release')],preexec_fn=nobody).returncode==0
fixture_root.chmod(0o700)
assert not can_read(), 'The old policy must reject nonroot traversal'
fixture_root.chmod(0o755)
assert can_read(), 'The corrected policy must permit nonroot traversal'
report={'scope':'Offline target-unit validation, ARM64 blkid and handoff-move failure fixtures; no PID1 or filesystem mounts run',
        'ramdisk_sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),
        'blkid_version':version.strip(),'target_units_verified':unit_names,
        'unit_check_root_is_separate_clone':True,'move_rollback_fixtures':fixtures,
        'packed_init_and_logger_match_sources':True,'original_container_readonly_policy_present':True,
        'ram_overlay_policy_present':True,'pid1_executed':False}
report['nonroot_directory_permission_fixture_passed']=True
report['packed_permission_policy_verified']=True
report['unit_verification_warnings_present']=bool((out/'unit-verification.log').read_text().strip())
report['known_existing_root_warning']='Legacy lower-root hostkey unit warning in offline clone; R5 normalizes it in RAM overlay before PID1'
(out/'userspace-precheck.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
