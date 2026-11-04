"""Delegate one bounded, tool-free review through the user's local Responses bridge."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import urllib.error
import urllib.request

P = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('--task-file', type=Path)
parser.add_argument('--output-name', default='initramfs-review')
parser.add_argument('--max-output-tokens', type=int, default=900)
args = parser.parse_args()
assert re.fullmatch(r'[a-z0-9][a-z0-9-]{0,63}', args.output_name)
assert 100 <= args.max_output_tokens <= 6000
config = Path(r'C:\Users\LIKImk\Documents\Codex\2026-10-29\completions-responses\outputs\responses-bridge\.env')
values = {}
for line in config.read_text(encoding='utf-8-sig').splitlines():
    match = re.match(r'^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$', line)
    if match:
        value = match[2].strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ['"', "'"]:
            value = value[1:-1]
        values[match[1]] = value
assert values.get('UPSTREAM_MODEL'), 'Bridge has no configured UPSTREAM_MODEL; choose a supported model first'
port = int(values.get('PORT', '8787'))
assert 1 <= port <= 65535
script = (P / 'armbian/initramfs/evaluation-init.sh').read_text(encoding='utf-8')
script = script.replace('614e0000-0000-4b53-8000-1d28000054a9', '<CONTAINER_PARTUUID>')
task = (args.task_file.read_text(encoding='utf-8') if args.task_file else
        '审查下列Linux评估initramfs脚本，列出最重要的3项待核查风险，区分确定问题和待验证项。背景：脚本原用于官方6.1.115，其SquashFS/overlay为模块；后续自定义6.1.172把两者内建。原Arch分区必须只读，rootfs用RAM overlay。\n\n' + script)
assert len(task.encode('utf-8')) <= 64000
payload = {
    'model': values['UPSTREAM_MODEL'], 'stream': False, 'max_output_tokens': args.max_output_tokens,
    'instructions': '你是独立的只读代码审查助手。只分析提供的内容，不调用工具，不执行命令，不假装测试过。严格区分已有证据与假设，不把脱敏占位当成真实代码缺陷。',
    'input': task,
}
headers = {'Content-Type': 'application/json'}
if values.get('BRIDGE_API_KEY'):
    headers['Authorization'] = 'Bearer ' + values['BRIDGE_API_KEY']
request = urllib.request.Request(f'http://127.0.0.1:{port}/v1/responses',
                                 data=json.dumps(payload, ensure_ascii=False).encode('utf-8'),
                                 headers=headers, method='POST')
out = P / 'analysis/armbian/bridge-review'
out.mkdir(parents=True, exist_ok=True)


def status(state, **details):
    record = {'task': args.output_name, 'state': state,
              'updated_at_utc': datetime.now(timezone.utc).isoformat(), **details}
    (out / (args.output_name + '.status.json')).write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


status('running')
try:
    with urllib.request.urlopen(request, timeout=180) as response:
        result = json.load(response)
except urllib.error.HTTPError as error:
    status('failed_http', http_status=error.code)
    raise SystemExit(f'Local bridge request failed with HTTP {error.code}; no response body or keys printed') from None
except urllib.error.URLError:
    status('failed_transport')
    raise SystemExit('Local bridge connection failed or timed out; no keys printed') from None
text = '\n'.join(part.get('text', '') for item in result.get('output', [])
                 if item.get('type') == 'message' for part in item.get('content', [])
                 if part.get('type') == 'output_text')
(out / (args.output_name + '.json')).write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
(out / (args.output_name + '.txt')).write_text(text + '\n', encoding='utf-8')
if result.get('status') != 'completed' or not text.strip():
    status('failed_empty_or_incomplete', response_status=result.get('status'), usage=result.get('usage'))
    raise SystemExit('Bridge returned no completed nonempty text; response saved for diagnosis, no work treated as completed')
status('completed', response_id=result.get('id'), usage=result.get('usage'), result_file=args.output_name + '.txt')
print(json.dumps({'status': result.get('status'), 'model': result.get('model'),
                  'usage': result.get('usage'), 'review': text,
                  'note': 'External model review only; no native Codex subagent or tool execution'}, ensure_ascii=False))
