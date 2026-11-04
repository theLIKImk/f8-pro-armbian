set -eu
python3 - <<'PY'
from pathlib import Path
import subprocess,re,json
p=Path('/opt/f8-pro/vendor-gpu-g13p0-20261028/lib')
exports=set()
for lib in p.iterdir():
 if '.so' in lib.name and not lib.is_symlink():
  text=subprocess.check_output(['nm','-D','--defined-only',str(lib)],text=True)
  exports.update(re.findall(r'\b((?:egl|gbm_)\w+)',text))
plugin=Path('/usr/lib/qt6/plugins/wayland-graphics-integration-client/libqt-plugin-wayland-egl.so')
text=subprocess.check_output(['readelf','--dyn-syms','--wide',str(plugin)],text=True)
required=set(re.findall(r'UND\s+(egl\w+)',text))
print(json.dumps({'qt_wayland_egl_required':sorted(required),'missing':sorted(required-exports),'platform_exports':sorted(s for s in exports if 'Platform' in s)},indent=2))
PY
