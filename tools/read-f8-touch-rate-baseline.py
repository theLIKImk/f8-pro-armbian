import json
from pathlib import Path
W=Path('/var/lib/f8-pro/touch-rate/baseline1')
result=json.loads((W/'result.json').read_text())
print(json.dumps({k:v for k,v in result.items() if k not in ['frames','irq_timestamps']},indent=2))
