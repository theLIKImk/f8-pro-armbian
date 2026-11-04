import importlib.util,json,re,subprocess
from pathlib import Path
root=Path(__file__).resolve().parent.parent
spec=importlib.util.spec_from_file_location('c',root/'tools/build-plasma-activities.py');c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
name='kwin';report=root/'analysis/plasma-6.7.5';work=json.loads((report/(name+'-native-build.json')).read_text())['remote_build_directory']
assert re.fullmatch('/home/alarm/f8-pro-builds/kwin-6.7.5-[A-Za-z0-9]{8}',work)
for filename in ['autogen-limit.json','autogen-limit-configure.log']:
    subprocess.run(['scp',*c.OPTIONS,c.HOST+':'+work+'/'+filename,str(report/(name+'-'+filename))],check=True,timeout=30)
print((report/'kwin-autogen-limit.json').read_text())
