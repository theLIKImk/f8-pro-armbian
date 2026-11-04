import json,re,time
from pathlib import Path
app=Path('/home/likimk/Applications/Phira-linux-arm64-v0.8.2');o={}
for p in sorted((app/'data/logs').glob('*')):
 if p.is_file() and p.stat().st_size<10*1024*1024:
  lines=p.read_text(errors='replace').splitlines();selected=[l for l in lines if re.search(r'ERROR|WARN|OpenGL|renderer|Phira|version',l,re.I)]
  o[p.name]={'bytes':p.stat().st_size,'relevant_lines':selected[:30]}
print(json.dumps({'logs':o},indent=2))
