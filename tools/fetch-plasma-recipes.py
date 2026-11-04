"""Collect historical official Arch recipes and a static Plasma dependency graph.

Reads .SRCINFO as data; never sources PKGBUILD or executes build/install scripts.
The graph remains a candidate until architecture changes and recipes are reviewed.
"""
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import argparse

PROJECT = Path(__file__).resolve().parent.parent
VERSION = '6.7.5'
CACHE = PROJECT/'downloads/plasma67-packaging'
REPORT = PROJECT/'analysis/plasma-6.7.5/recipe-dependencies.json'


def git(*args):
    return subprocess.run(['git', '-c', 'http.lowSpeedLimit=100', '-c',
                           'http.lowSpeedTime=30', *args], check=True,
                          capture_output=True, text=True, timeout=180).stdout.strip()


def collect(name):
    assert re.fullmatch(r'[a-z0-9-]+', name)
    url = 'https://gitlab.archlinux.org/archlinux/packaging/packages/'+name+'.git'
    destination = CACHE/name
    if not destination.exists():
        refs = git('ls-remote', '--tags', url, VERSION+'-*')
        tags = re.findall(r'refs/tags/('+re.escape(VERSION)+r'-(\d+))$', refs, re.M)
        if not tags:
            raise ValueError('No exact release tag for '+name)
        tag = max(tags, key=lambda item: int(item[1]))[0]
        temporary = Path(tempfile.mkdtemp(prefix='.fetching-'+name+'-', dir=CACHE))
        git('clone', '--depth', '1', '--branch', tag, url, str(temporary))
        temporary.rename(destination)
    else:
        tag = git('-C', str(destination), 'describe', '--tags', '--exact-match', 'HEAD')
    if not re.fullmatch(re.escape(VERSION)+r'-\d+', tag):
        raise ValueError('Unexpected existing checkout tag for '+name)
    commit = git('-C', str(destination), 'rev-parse', 'HEAD')
    raw = git('-C', str(destination), 'show', 'HEAD:.SRCINFO')
    fields = {}
    for line in raw.splitlines():
        if ' = ' in line:
            key, value = line.split(' = ', 1)
            key, value = key.strip(), value.strip()
            fields.setdefault(key, []).append(value)
    if fields.get('pkgver') != [VERSION]:
        raise ValueError('Recipe version mismatch for '+name)
    dependency_fields = {key: values for key, values in fields.items()
                         if key == 'depends' or key == 'makedepends'
                         or key.startswith(('depends_', 'makedepends_'))}
    return {'repository': url, 'tag': tag, 'commit': commit,
            'upstream_tag_signature_verified': False,
            'recipe_execution_review_complete': False,
            'architectures': fields.get('arch', []), 'package_names': fields.get('pkgname', []),
            'dependency_fields': dependency_fields,
            'dependencies': sorted({re.split(r'[<>=]', value)[0]
                                    for values in dependency_fields.values() for value in values}),
            'source_fields': fields.get('source', []), 'install_scripts': fields.get('install', [])}


def main():
    if sys.platform != 'linux':
        raise SystemExit('Run inside build WSL')
    CACHE.mkdir(parents=True, exist_ok=True)
    release = json.loads((PROJECT/'analysis/plasma-6.7.5/sources.json').read_text())['packages']
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--extra-roots',nargs='*',default=[])
    args=parser.parse_args()
    assert set(args.extra_roots)<=release.keys()
    aliases = {'plasma-x11-session': 'plasma-workspace', 'plasma5-integration': 'plasma-integration'}
    # The official source name and Arch package/repository name differ.
    source_names = {'polkit-kde-agent': 'polkit-kde-agent-1'}
    recipes, errors = {}, {}
    pending = {'plasma-workspace', 'plasma-desktop', 'kwin', 'kwin-x11',*args.extra_roots}
    def save():
        temporary=REPORT.with_suffix('.json.partial')
        temporary.write_text(json.dumps({'version': VERSION, 'recipes': recipes,
            'errors': errors, 'complete_dependency_closure_validated': False,
            'note': 'Static candidate graph only. Recipes and aarch64 changes require review; no recipe executed.'}, indent=2)+'\n')
        temporary.replace(REPORT)
    with ThreadPoolExecutor(max_workers=4) as pool:
        while pending:
            current, pending = pending, set()
            futures = {pool.submit(collect, name): name for name in current}
            for future in as_completed(futures):
                name = futures[future]
                try:
                    recipes[name] = future.result()
                    print(name+': exact release recipe recorded', flush=True)
                    for dependency in recipes[name]['dependencies']:
                        mapped = aliases.get(dependency, dependency)
                        if source_names.get(mapped,mapped) in release and mapped not in recipes and mapped not in current and mapped not in errors:
                            pending.add(mapped)
                except Exception as error:
                    errors[name] = type(error).__name__+': '+str(error)[:1000]
                    print(name+': fetch failed; see report', flush=True)
                save()
    print('Recorded recipes: '+str(len(recipes))+'; errors: '+str(len(errors)), flush=True)
    return bool(errors)


if __name__ == '__main__':
    raise SystemExit(main())
