"""Fetch official Plasma 6.7.5 metadata and verify selected source archives.

No source extraction, execution or package installation. Isolated GPG keyring.
"""
import argparse
import hashlib
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
import subprocess
import urllib.parse
import urllib.request

PROJECT = Path(__file__).resolve().parent.parent
VERSION = '6.7.5'
INFO = 'https://kde.org/info/plasma-6.7.5/'
KEYS = 'https://kde.org/info/plasma-signing-keys.pgp'
SIGNER = '0AAC775BB6437A8D9AF7A3ACFE0784117FBCE11D'


class HTTPSOnly(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if urllib.parse.urlparse(newurl).scheme != 'https':
            raise ValueError('Refusing non-HTTPS redirect')
        return super().redirect_request(req, fp, code, msg, headers, newurl)


OPENER = urllib.request.build_opener(HTTPSOnly())


def fetch(url, limit):
    request = urllib.request.Request(url, headers={'User-Agent': 'F8-PRO-source-verifier/1.0'})
    with OPENER.open(request, timeout=60) as response:
        data = response.read(limit+1)
    if len(data) > limit:
        raise ValueError('Download exceeds expected maximum size')
    return data


class Rows(HTMLParser):
    def __init__(self):
        super().__init__()
        self.rows, self.row = [], None

    def handle_starttag(self, tag, attrs):
        if tag == 'tr':
            self.row = {'links': [], 'text': ''}
        elif tag == 'a' and self.row is not None:
            self.row['links'].extend(v for k,v in attrs if k == 'href')

    def handle_data(self, text):
        if self.row is not None:
            self.row['text'] += text+' '

    def handle_endtag(self, tag):
        if tag == 'tr' and self.row is not None:
            self.rows.append(self.row)
            self.row = None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--packages', nargs='*', default=['libplasma', 'kwin', 'kwin-x11', 'plasma-workspace'])
    args = parser.parse_args()
    os.umask(0o077)
    cache = PROJECT/'downloads/plasma-6.7.5'
    report = PROJECT/'analysis/plasma-6.7.5'
    cache.mkdir(parents=True, exist_ok=True)
    report.mkdir(parents=True, exist_ok=True)
    html = fetch(INFO, 2*1024**2).decode('utf-8')
    if SIGNER not in html:
        raise ValueError('Official release metadata does not confirm pinned signer')
    rows = Rows()
    rows.feed(html)
    packages = {}
    for row in rows.rows:
        hashes = re.findall(r'\b[0-9a-f]{64}\b', row['text'])
        for href in row['links']:
            url = urllib.parse.urljoin(INFO, href)
            parsed = urllib.parse.urlparse(url)
            # The HTTPS release page still publishes legacy HTTP download links.
            # Upgrade only this exact official host; redirects remain HTTPS-only.
            if parsed.scheme == 'http' and parsed.hostname == 'download.kde.org':
                parsed = parsed._replace(scheme='https')
                url = urllib.parse.urlunparse(parsed)
            match = re.fullmatch(r'/stable/plasma/6\.7\.5/([a-z0-9-]+)-6\.7\.5\.tar\.xz', parsed.path)
            if parsed.scheme == 'https' and parsed.hostname == 'download.kde.org' and match:
                if len(hashes) != 1 or match[1] in packages:
                    raise ValueError('Ambiguous official source row')
                packages[match[1]] = {'url': url, 'sha256': hashes[0], 'signature_url': url+'.sig', 'signature_verified': False}
    required = {'libplasma', 'kwin', 'kwin-x11', 'plasma-workspace', 'plasma-desktop'}
    if not required <= packages.keys() or not set(args.packages) <= packages.keys():
        raise ValueError('Official source list incomplete or requested component unknown')
    manifest = {'version': VERSION, 'official_info_url': INFO, 'pinned_primary_signer': SIGNER,
                'official_keyring_url': KEYS, 'packages': packages,
                'complete_dependency_closure_validated': False, 'arm64_build_tested': False}
    # Recheck previously verified archives too, rather than losing their status
    # when a later invocation adds more components or trusting stale flags.
    previous_path = report/'sources.json'
    if previous_path.exists():
        previous = json.loads(previous_path.read_text())
        if previous.get('version') == VERSION and previous.get('pinned_primary_signer') == SIGNER:
            args.packages = list(dict.fromkeys(args.packages + [
                name for name, record in previous.get('packages', {}).items()
                if record.get('signature_verified') and name in packages
            ]))
    def save():
        temporary=report/'sources.json.partial'
        temporary.write_text(json.dumps(manifest, indent=2)+'\n')
        temporary.replace(report/'sources.json')
    save()
    print(f'Official source rows: {len(packages)}; signer pinned', flush=True)
    keyring = cache/'plasma-signing-keys.pgp'
    keyring.write_bytes(fetch(KEYS, 2*1024**2))
    home = Path('/var/tmp/f8-pro-archlinux-20261027/plasma-verification-20261028')
    home.mkdir(mode=0o700, exist_ok=True)
    home.chmod(0o700)
    gpg = ['gpg', '--batch', '--homedir', str(home)]
    subprocess.run(gpg+['--import', str(keyring)], capture_output=True, check=True)
    fingerprints = subprocess.run(gpg+['--with-colons', '--fingerprint', SIGNER], capture_output=True, text=True, check=True).stdout
    if 'fpr:::::::::'+SIGNER+':' not in fingerprints:
        raise ValueError('Pinned primary key not present in imported official keyring')
    for name in args.packages:
        record = packages[name]
        archive = cache/(name+'-'+VERSION+'.tar.xz')
        if archive.exists():
            data = archive.read_bytes()
        else:
            data = fetch(record['url'], 128*1024**2)
            if hashlib.sha256(data).hexdigest() != record['sha256']:
                raise ValueError('Source archive SHA-256 mismatch')
            archive.write_bytes(data)
        if hashlib.sha256(data).hexdigest() != record['sha256']:
            raise ValueError('Cached source archive SHA-256 mismatch')
        signature = archive.with_suffix(archive.suffix+'.sig')
        signature.write_bytes(fetch(record['signature_url'], 65536))
        verified = subprocess.run(gpg+['--status-fd=1', '--verify', str(signature), str(archive)], capture_output=True, text=True)
        valid = [line.split()[2:] for line in verified.stdout.splitlines() if line.startswith('[GNUPG:] VALIDSIG ')]
        if verified.returncode or not any(SIGNER in (fields[0], fields[-1]) for fields in valid):
            raise ValueError('Source signature did not validate against pinned release signer')
        record['signature_verified'] = True
        record['sha256_verified'] = True
        record['size_bytes'] = len(data)
        (report/(name+'-gpg-status.txt')).write_text(verified.stdout)
        save()
        print(name+': SHA-256 and pinned OpenPGP signature PASS', flush=True)


if __name__ == '__main__':
    main()
