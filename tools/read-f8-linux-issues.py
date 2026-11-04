import json,os,subprocess,re
from pathlib import Path
assert os.geteuid()==0 and os.environ.get('SUDO_USER')=='likimk'
out={}
def read(name,args,timeout=12):
 try:
  p=subprocess.run(args,capture_output=True,text=True,timeout=timeout);out[name]={'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr}
 except subprocess.TimeoutExpired:out[name]={'timeout':True}
 except OSError as e:out[name]={'unavailable':str(e)}
u=['runuser','-u','likimk','--','env','XDG_RUNTIME_DIR=/run/user/1602','DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1602/bus','WAYLAND_DISPLAY=wayland-0']
read('mic_controls',['amixer','-c','0','scontents'])
read('ucm',['cat','/usr/share/alsa/ucm2/F8-PRO/HiFi.conf'])
read('pipewire_status',u+['wpctl','status'])
read('mic_volume',u+['wpctl','get-volume','@DEFAULT_AUDIO_SOURCE@'])
read('polkit_process',['pgrep','-af','polkit|authentication-agent'])
read('polkit_system_log',['journalctl','-b','-u','polkit.service','--no-pager','-n','90'])
read('polkit_user_log',['journalctl','-b','_UID=1602','--no-pager','--grep','polkit|authentication|segfault|assert|crash','-n','100'])
read('cores',['coredumpctl','list','--no-pager','--since','today'])
read('kwin_support',u+['qdbus6','org.kde.KWin','/KWin','supportInformation'])
read('packages',['dpkg-query','-W','polkit-kde-agent-1','polkitd','libpam0g','pipewire','wireplumber','libegl-mesa0','libgl1-mesa-dri','plasma-workspace'])
read('dmesg_perf',['sh','-c','dmesg | grep -iE "cpufreq|devfreq|panthor|thermal|regulator|opp" | tail -100'])
read('clk',['sh','-c','cat /sys/kernel/debug/clk/clk_summary | grep -E "armclk|b[01]pll|lpll|gpu|gpll"'])
out['cmdline']=Path('/proc/cmdline').read_text().strip()
out['cpufreq']={str(p):{f.name:f.read_text().strip() for f in p.iterdir() if f.name in ['scaling_governor','scaling_cur_freq','scaling_min_freq','scaling_max_freq','cpuinfo_min_freq','cpuinfo_max_freq','scaling_available_frequencies']} for p in Path('/sys/devices/system/cpu/cpufreq').glob('policy*')}
out['devfreq']={str(p):{n:(p/n).read_text().strip() for n in ['name','governor','cur_freq','min_freq','max_freq','available_frequencies','available_governors','trans_stat'] if (p/n).is_file()} for p in Path('/sys/class/devfreq').glob('*')}
out['thermal']=[{'type':(p/'type').read_text().strip(),'temp':(p/'temp').read_text().strip()} for p in Path('/sys/class/thermal').glob('thermal_zone*')]
print(json.dumps(out,indent=2))
