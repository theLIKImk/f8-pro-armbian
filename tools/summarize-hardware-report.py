"""Read a returned collector tar.gz and summarize evidence without extracting it.

Archive contents are treated as data. No commands in logs are executed.
"""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import tarfile


def summarize(source):
    sessions = {}
    with tarfile.open(source, 'r:*') as archive:
        members = archive.getmembers()
        if len(members) > 4096 or sum(max(m.size, 0) for m in members) > 256 * 1024 * 1024:
            raise ValueError('Report exceeds expected collection size')
        seen = set()
        for member in members:
            path = PurePosixPath(member.name)
            if path.is_absolute() or '..' in path.parts or '\\' in member.name:
                raise ValueError('Unsafe report path: ' + member.name)
            if not member.isdir() and not member.isfile():
                raise ValueError('Links and special files are not accepted')
            if member.name in seen:
                raise ValueError('Duplicate report member: ' + member.name)
            seen.add(member.name)
            if not member.isfile():
                continue
            if member.size > 32 * 1024 * 1024:
                raise ValueError('Unexpectedly large log: ' + member.name)
            wanted = {'kernel.txt', 'os-release.txt', 'board-model.txt', 'block-bytes.txt',
                      'renderer-gl.txt', 'session-type.txt', 'check-status.tsv', 'live.dtb'}
            if path.name not in wanted:
                continue
            with archive.extractfile(member) as stream:
                payload = stream.read()
            session = sessions.setdefault(str(path.parent), {})
            if path.name == 'live.dtb':
                session['live_dtb'] = {'bytes': len(payload), 'sha256': hashlib.sha256(payload).hexdigest()}
                continue
            value = payload.decode('utf-8', 'replace').replace('\0', '').strip()
            session[path.stem] = value
            if path.name == 'renderer-gl.txt':
                session['software_renderer_evidence'] = bool(re.search(r'llvmpipe|softpipe|lavapipe', value, re.I))
            if path.name == 'check-status.tsv':
                session['checks_requiring_review'] = [line for line in value.splitlines()[1:]
                                                      if not line.endswith('\tran\t0')]
    with source.open('rb') as stream:
        digest = hashlib.file_digest(stream, 'sha256').hexdigest()
    return {'source': str(source), 'archive_sha256': digest, 'sessions': sessions,
            'hardware_automatically_approved': False,
            'note': 'Missing tools and nonzero command exits require review; no hardware is marked working from collection alone.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archive', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    report = summarize(args.archive)
    with args.output.open('x', encoding='utf-8') as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print('Summary written:', args.output)
