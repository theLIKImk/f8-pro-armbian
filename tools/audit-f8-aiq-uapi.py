"""Offline normalize RKAIQ-shipped UAPI headers against official kernel headers."""
import difflib,json,re
from pathlib import Path
P=Path(__file__).resolve().parents[1]
a=Path('/var/tmp/f8-pro-armbian/camera-aiq-audit/seeed/usr/include/rkaiq/common')
b=Path('/var/tmp/f8-pro-armbian/official-kernel/usr/src/linux-headers-6.1.115-vendor-rk35xx/include/uapi/linux')
out=P/'analysis/armbian/camera/c4/aiq-uapi';out.mkdir(exist_ok=True)
def norm(s):
    s=re.sub(r'\b__(u|s)(8|16|32|64)\b',r'\1\2',s)
    s=s.replace('rk-isp','rkisp').replace('_RK_ISP','_RKISP')
    return [line.strip() for line in s.splitlines() if line.strip() and not line.strip().startswith(('#include','/*','*','//'))]
report={}
for old,new in [('rkisp3-config.h','rk-isp3-config.h'),('rkisp21-config.h','rk-isp21-config.h'),('rkisp2-config.h','rk-isp2-config.h'),('rk-camera-module.h','rk-camera-module.h')]:
    x=norm((a/old).read_text());y=norm((b/new).read_text())
    diff=list(difflib.unified_diff(x,y,fromfile='AIQ/'+old,tofile='kernel/'+new))
    (out/(old+'.diff')).write_text('\n'.join(diff)+'\n')
    report[old]={'normalized_equal':x==y,'diff_lines':len(diff)}
(out/'summary.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
