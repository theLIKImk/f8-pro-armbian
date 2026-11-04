import json
d = json.load(open('/run/user/1601/f8-camera-preview-status.json'))
print('state:', d.get('state'))
print('frames:', d.get('frames'))
print('engine_pid:', d.get('engine_pid'))
print('capture_pid:', d.get('capture_pid'))
print('last_error:', repr(d.get('last_error'))[:100])
log = d.get('engine_log', '')
for line in log.splitlines():
    if any(x in line for x in ['READY', 'start success', 'init success', 'prepare success', 'ERROR', 'failed']):
        print('  log:', line[:120])
