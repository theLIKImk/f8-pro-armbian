from pathlib import Path
import importlib.util,hashlib
root=Path(__file__).resolve().parent.parent
spec=importlib.util.spec_from_file_location('source_fetch',root/'tools/fetch-plasma-sources.py');fetcher=importlib.util.module_from_spec(spec);spec.loader.exec_module(fetcher)
url='https://invent.kde.org/plasma/powerdevil/-/commit/54f8a4a8.patch'
expected='f92b339712096d623c862e31b58d87ce72f381462efeab30893f1937a6634f88'
data=fetcher.fetch(url,1024*1024)
assert hashlib.sha256(data).hexdigest()==expected
output=root/'downloads/plasma-6.7.5/powerdevil-54f8a4a8.patch';output.write_bytes(data)
print(data.decode())
