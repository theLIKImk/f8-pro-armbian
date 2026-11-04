import json,os,subprocess
assert os.geteuid()==0 and os.environ.get('SUDO_USER')=='likimk'
args=['apt-get','-s','install','--no-install-recommends','cmake','extra-cmake-modules','qt6-base-dev','libksysguard-dev','libkf6coreaddons-dev','libkf6i18n-dev','libkf6solid-dev','libkf6kio-dev','libudev-dev','libsensors-dev']
r=subprocess.run(args,capture_output=True,text=True,timeout=25)
print(json.dumps({'exit':r.returncode,'stdout':r.stdout,'stderr':r.stderr}))
