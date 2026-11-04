import json,os,pwd,subprocess
from pathlib import Path
uid=pwd.getpwnam('likimk').pw_uid;o={'processes':[],'plugins':[]}
for p in Path('/proc').glob('[0-9]*'):
 try:
  if p.stat().st_uid==uid and str((p/'exe').resolve()).startswith('/home/likimk/Applications/Phira-linux-arm64-v0.8.2/'):
   o['processes'].append({'pid':int(p.name),'exe':str((p/'exe').resolve())})
 except OSError:pass
for p in Path('/usr/lib/aarch64-linux-gnu/alsa-lib').glob('*'):
 if p.name in ['libasound_module_pcm_pipewire.so','libasound_module_pcm_pulse.so']:o['plugins'].append(str(p))
for f in ['/etc/asound.conf','/home/likimk/.asoundrc']:
 p=Path(f)
 if p.exists():o[f]=p.read_text()[:5000]
print(json.dumps(o,indent=2))
