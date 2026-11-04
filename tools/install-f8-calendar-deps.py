import subprocess,json

def run(a):
 r=subprocess.run(a,capture_output=True,text=True,timeout=12);return dict(exit=r.returncode,stdout=r.stdout,stderr=r.stderr)
print(json.dumps({'policy':run(['apt-cache','policy','plasma-calendar-addons']),'details':run(['apt-cache','show','plasma-calendar-addons']),'install':run(['systemd-run','--unit=f8-calendar-deps','--collect','--setenv=DEBIAN_FRONTEND=noninteractive','/usr/bin/apt-get','-y','--no-install-recommends','install','plasma-calendar-addons'])}))
