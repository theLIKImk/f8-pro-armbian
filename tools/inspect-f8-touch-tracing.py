import hashlib,json,os
from pathlib import Path
assert os.geteuid()==0
out={}
for root in ['/sys/kernel/tracing','/sys/kernel/debug/tracing']:
 p=Path(root);out[root]={n:(p/n).exists() for n in ['kprobe_events','instances','available_filter_functions','trace_clock']}
 if (p/'available_filter_functions').exists():out[root]['gsl_functions']=[l for l in (p/'available_filter_functions').read_text().splitlines() if 'gsl_alg_id_main' in l or 'gsl_mask_tiaoping' in l]
p=Path('/usr/libexec/f8-pro/f8_gsl_shuping.ko');out['module_sha256']=hashlib.sha256(p.read_bytes()).hexdigest()
out['active_srcversion']=Path('/sys/module/f8_gsl_shuping/srcversion').read_text().strip()
print(json.dumps(out,indent=2))
