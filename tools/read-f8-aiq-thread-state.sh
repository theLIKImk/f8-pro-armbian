#!/bin/sh
set -eu
python3 -I - <<'PY'
import json,subprocess,resource,os
from pathlib import Path
checks={}
for key,args in {'strace':['sh','-c','command -v strace'],
 'caps':['sh','-c','grep -E "Cap|Threads|Seccomp" /proc/self/status; cat /proc/self/cgroup; command -v capsh >/dev/null && capsh --print'],
 'rt':['sh','-c','cat /proc/sys/kernel/sched_rt_runtime_us /proc/sys/kernel/threads-max; cat /proc/self/limits'],
 'stats':['v4l2-ctl','-d','/dev/video29','--all']}.items():
 p=subprocess.run(args,capture_output=True,text=True,timeout=8);checks[key]={'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr}
try:os.sched_setscheduler(0,os.SCHED_FIFO,os.sched_param(10));rt_test='ok';os.sched_setscheduler(0,os.SCHED_OTHER,os.sched_param(0))
except Exception as e:rt_test=str(e)
print(json.dumps({'checks':checks,'self_rt_test':rt_test,'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip()},indent=2))
PY
