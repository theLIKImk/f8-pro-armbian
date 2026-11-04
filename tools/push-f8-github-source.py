"""Push the audited snapshot with transient HTTP authentication from stdin."""
from pathlib import Path
import os,sys,json,base64,subprocess,urllib.request
P=Path(__file__).resolve().parents[1];W=P/'local/github-publish-20261104';R=W/'repository'
token=sys.stdin.read().strip();assert token
assert json.loads((W/'source-audit.json').read_text())['credential_pattern_scan_passed']
env=dict(os.environ,GIT_TERMINAL_PROMPT='0',GIT_CONFIG_COUNT='3',GIT_TRACE='0',GIT_TRACE_CURL='0',GIT_CURL_VERBOSE='0')
env.update(GIT_CONFIG_KEY_0='http.proxy',GIT_CONFIG_VALUE_0='',GIT_CONFIG_KEY_1='http.https://github.com/.extraheader',GIT_CONFIG_VALUE_1='Authorization: Basic '+base64.b64encode(('x-access-token:'+token).encode()).decode(),GIT_CONFIG_KEY_2='credential.helper',GIT_CONFIG_VALUE_2='')
try:
 result=subprocess.run(['git','-C',str(R),'push','origin','HEAD:main'],env=env,capture_output=True,text=True,timeout=600)
 if result.returncode:raise RuntimeError(result.stderr.replace(token,'[REDACTED]'))
 commit=subprocess.check_output(['git','-C',str(R),'rev-parse','HEAD'],text=True).strip()
 req=urllib.request.Request('https://api.github.com/repos/theLIKImk/f8-pro-armbian/git/ref/heads/main',headers={'Authorization':'Bearer '+token,'User-Agent':'F8-publisher'})
 with urllib.request.urlopen(req,timeout=60) as response:remote=json.load(response)
 assert remote['object']['sha']==commit
 record={'commit':commit,'branch':'main','remote_ref_verified':True,'url':'https://github.com/theLIKImk/f8-pro-armbian'}
 (W/'source-pushed.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
 print(json.dumps(record))
finally:
 env.pop('GIT_CONFIG_VALUE_1',None);token=None
