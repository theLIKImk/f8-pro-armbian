"""Record R3 SMP, console and readonly userspace results from saved logs."""
import hashlib
import json
from pathlib import Path
import re

P=Path(__file__).resolve().parents[1]
logs=P/'local/hardware/armbian-6.1-r3-20261029-01'
def read(name):return (logs/name).read_text()
dmesg=read('DMESG.TXT')
assert 'SMP: Total of 8 processors activated.' in dmesg
assert read('CPUONLINE.TXT').strip()=='0-7' and read('CPUPOSS.TXT').strip()=='0-7'
assert 'ttyS2' in read('CONSOLE.TXT') and 'console [ttyS2] enabled' in dmesg
assert 'F8 R3 SMP AND READONLY USERSPACE SNAPSHOT COMPLETE' in dmesg
assert 'initcall rockchip_cpufreq_driver_init blacklisted' in dmesg
mount=next(line for line in read('MOUNTS.TXT').splitlines() if line.startswith('/dev/mmcblk0p6 '))
fields=mount.split();opts=set(fields[3].split(','))
assert fields[1]=='/run/original-root' and fields[2]=='ext4' and 'ro' in opts and 'norecovery' in opts
assert 'unmounting filesystem' in dmesg
assert read('RUNTRUE.TXT').strip()=='exit_code=0'
assert 'systemd 262' in read('RUNSYS.TXT') and read('RUNSYS.TXT').rstrip().endswith('exit_code=0')
assert 'ID=archarm' in read('ROOTPROBE.TXT')
files=[{'name':p.name,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
       for p in sorted(logs.iterdir()) if p.is_file() and p.suffix.upper() in ['.TXT','.BIN']]
report={'scope':'R3 real SMP/console/read-only original Arch basic binary tests, not PID1 or Armbian desktop acceptance',
 'date':'2026-10-29','source_directory':str(logs),'files':files,
 'candidate_sha256':'16c32f21ab9deba9550b04a8933bbe22a4ffb2d61f2c196bce4dfa924c852000',
 'kernel_release':'6.1.172-f8-pro-armbian-eval','online_cpus':'0-7','active_console':'ttyS2',
 'external_uart_rx_tx_tested':False,'vendor_cpufreq_initcall_skipped':True,'dvfs_or_stress_tested':False,
 'root_partition_mount_line':mount,'root_partition_unmounted':True,
 'arch_true_exit_code':0,'arch_systemd_version_exit_code':0,
 'arch_systemd_warning_present':'Function not implemented' in read('RUNSYS.TXT'),
 'arch_systemd_warning_resolved':False,'systemd_pid1_started':False,
 'armbian_userspace_started':False,'desktop_started':False,'charging_tested':False,
 'panic_or_oops_in_snapshot':bool(re.search(r'Kernel panic|Oops:',dmesg)),
 'host_volume_observed':'F: F861R3','snapshot_end_seconds':8.947640,
 'note':'PARTS.TXT was captured before MMC enumeration; successful p6 mount and later dmesg provide storage evidence'}
(logs/'test-result.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:report[k] for k in ['online_cpus','active_console','arch_true_exit_code',
 'arch_systemd_version_exit_code','arch_systemd_warning_present','systemd_pid1_started','panic_or_oops_in_snapshot']},ensure_ascii=False))
