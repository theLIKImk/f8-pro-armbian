"""Read-only board state and validated limits shared by UI and root helper."""
import json,os
from pathlib import Path

CONFIG=Path('/etc/f8-pro/performance-limits.json')
DEVICES={
 'gpu':('GPU · Mali-G610',Path('/sys/class/devfreq/fb000000.gpu-panthor'),1_000_000,1000),
 'cpu0':('小核 · A55 · CPU 0–3',Path('/sys/devices/system/cpu/cpufreq/policy0'),1000,1800),
 'cpu4':('大核组 1 · A76 · CPU 4–5',Path('/sys/devices/system/cpu/cpufreq/policy4'),1000,2400),
 'cpu6':('大核组 2 · A76 · CPU 6–7',Path('/sys/devices/system/cpu/cpufreq/policy6'),1000,2400),
}
def text(p):return Path(p).read_text().strip()
def profile():
 st=CONFIG.stat()
 if CONFIG.is_symlink() or st.st_uid!=0 or st.st_mode&0o022:raise ValueError('频率配置权限不正确')
 d=json.loads(CONFIG.read_text())
 if d.get('version')!=1:raise ValueError('频率配置版本不支持')
 return d
def limits():return profile()['validated_max_mhz']
def snapshot(key):
 if key not in DEVICES:raise ValueError('未知设备')
 title,p,scale,goal=DEVICES[key];s={'key':key,'title':title,'goal_mhz':goal,'enabled':False}
 if not p.exists():return dict(s,reason='调频接口尚未启用')
 isgpu=key=='gpu';n=lambda cpu,gpu:gpu if isgpu else cpu
 try:
  ceiling=limits().get(key,0)
  if not isgpu and text(p/'scaling_driver') not in {'f8-p2-fixedvolt','f8-p3-rk-opp'}:return dict(s,reason='当前 CPU 驱动尚未验证')
  raw=sorted(set(int(v) for v in text(p/n('scaling_available_frequencies','available_frequencies')).split()))
  allowed=[v for v in raw if v<=ceiling*scale]
  if not allowed:return dict(s,reason='等待频率档位验证')
  s.update(enabled=True,scale=scale,allowed=allowed,validated_mhz=allowed[-1]/scale,
   current=int(text(p/n('scaling_cur_freq','cur_freq'))),minimum=int(text(p/n('scaling_min_freq','min_freq'))),
   maximum=int(text(p/n('scaling_max_freq','max_freq'))),governor=text(p/n('scaling_governor','governor')),
   governors=text(p/n('scaling_available_governors','available_governors')).split())
 except (OSError,ValueError,KeyError) as e:return dict(s,enabled=False,reason=str(e))
 return s
def temperatures():
 out={}
 for p in Path('/sys/class/thermal').glob('thermal_zone*'):
  try:out[text(p/'type')]=int(text(p/'temp'))/1000
  except (OSError,ValueError):pass
 return out
def validate(s,mode,low=None,high=None):
 if not s['enabled']:raise ValueError(s.get('reason','设备不可用'))
 allowed=s['allowed']
 if mode=='auto':low,high=allowed[0],allowed[-1]
 elif mode not in {'fixed','range'}:raise ValueError('未知调频模式')
 if type(low) is not int or type(high) is not int or low not in allowed or high not in allowed or low>high:raise ValueError('请选择已开放档位且最低频率不超过最高频率')
 if mode=='fixed' and low!=high:raise ValueError('固定频率必须选择同一档位')
 preferred=['simple_ondemand'] if s['key']=='gpu' else ['ondemand']
 governor=next((g for g in preferred if g in s['governors']),None)
 if governor is None:raise ValueError('当前驱动缺少已验证的自动调频策略')
 return {'key':s['key'],'mode':mode,'minimum':low,'maximum':high,'governor':governor}
