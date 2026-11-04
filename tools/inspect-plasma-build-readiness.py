"""Read-only build prerequisite inventory for the next reviewed Plasma recipes."""
from pathlib import Path
import importlib.util,json,re,shlex,subprocess
root=Path(__file__).resolve().parent.parent
spec=importlib.util.spec_from_file_location('connection',root/'tools/build-plasma-activities.py');c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
graph=json.loads((root/'analysis/plasma-6.7.5/recipe-dependencies.json').read_text())
family=set(json.loads((root/'analysis/plasma-6.7.5/sources.json').read_text())['packages'])
for recipe in graph['recipes'].values():family.update(recipe['package_names'])
packages=['kactivitymanagerd','kde-cli-tools','libksysguard','ksystemstats','plasma5support','systemsettings','kmenuedit','polkit-kde-agent','kscreen','plasma-workspace','xdg-desktop-portal-kde','powerdevil','plasma-desktop']
report={}
for name in packages:
    dependencies=graph['recipes'][name]['dependencies']
    assert all(re.fullmatch(r'[a-zA-Z0-9+_.-]+',d) for d in dependencies)
    result=c.ssh('pacman -T '+' '.join(shlex.quote(d) for d in dependencies),capture_output=True,text=True,timeout=30)
    assert result.returncode in (0,127),(name,result.stderr)
    missing=result.stdout.splitlines()
    report[name]={'missing_plasma_components':[d for d in missing if d in family],'missing_external_dependencies':[d for d in missing if d not in family]}
output={'note':'Read-only candidate inventory from upstream union of split-package build/runtime dependencies. Reviewed staging recipes may defer runtime-only cycle dependencies. No installation performed.','packages':report}
(root/'analysis/plasma-6.7.5/build-readiness.json').write_text(json.dumps(output,indent=2)+'\n')
print(json.dumps(output,indent=2))
