"""Read an F8BOOTLOG directory; inspect GPT CRCs and native execution probes.

Never modifies the diagnostic volume, storage or system configuration.
"""
import argparse
import json
from pathlib import Path
import re
import struct
import uuid
import zlib


def parse_gpt(data):
    data = bytes(data)
    if len(data) < 1024 or data[512:520] != b'EFI PART':
        raise ValueError('Missing primary GPT header')
    header = data[512:1024]
    size, checksum = struct.unpack_from('<II', header, 12)
    if not 92 <= size <= 512:
        raise ValueError('Invalid GPT header size')
    checked = bytearray(header[:size])
    checked[16:20] = b'\0'*4
    if zlib.crc32(checked) != checksum:
        raise ValueError('GPT header CRC mismatch')
    lba, count, item_size, entries_crc = struct.unpack_from('<QIII', header, 72)
    if not 0 < count <= 1024 or not 128 <= item_size <= 4096:
        raise ValueError('Invalid GPT entry dimensions')
    start, end = lba*512, lba*512+count*item_size
    if end > len(data):
        raise ValueError('GPT entries are outside captured metadata')
    entries = data[start:end]
    if zlib.crc32(entries) != entries_crc:
        raise ValueError('GPT entry array CRC mismatch')
    result = []
    for i in range(count):
        row = entries[i*item_size:(i+1)*item_size]
        if row[:16] == b'\0'*16:
            continue
        first, last = struct.unpack_from('<QQ', row, 32)
        if last < first:
            raise ValueError('Invalid GPT partition bounds')
        name = row[56:128].decode('utf-16-le', 'replace').split('\0', 1)[0]
        result.append({'index': i+1, 'name': name, 'start_lba': first,
                       'sectors': last-first+1, 'partuuid': str(uuid.UUID(bytes_le=row[16:32]))})
    return result


def summarize(directory):
    directory = Path(directory)
    if not directory.is_dir() or not (directory/'ROOTFS.TXT').is_file():
        raise FileNotFoundError('Diagnostic directory or ROOTFS.TXT is unavailable; do not infer a boot failure')
    def read(name):
        p = directory/name
        if not p.is_file():
            return ''
        if p.stat().st_size > 1024*1024:
            raise ValueError('Unexpectedly large diagnostic text')
        return p.read_text(encoding='utf-8', errors='replace')
    root = read('ROOTFS.TXT')
    result = {'rootfs_readonly_mount_ok': root.startswith('ROOTFS READONLY MOUNT OK'),
              'arch_rootfs_detected': 'ID=archarm' in root,
              'native_probes': {}, 'gpt_available': False,
              'arch_pid1_boot_verified': False}
    for name in ('RUNTRUE.TXT', 'RUNINIT.TXT', 'RUNSYS.TXT'):
        text = read(name)
        if not text:
            continue
        status = re.search(r'(?m)^exit_code=(\d+)\s*$', text)
        result['native_probes'][name] = {
            'exit_code': int(status[1]) if status else None,
            'output': text[:2000].strip()
        }
    metadata = directory/'GPT.BIN'
    if metadata.is_file():
        if metadata.stat().st_size > 1024*1024:
            raise ValueError('Unexpectedly large GPT capture')
        partitions = parse_gpt(metadata.read_bytes())
        result['gpt_available'] = True
        result['gpt_crc_checked'] = True
        result['partitions'] = partitions
        token = re.search(r'\broot=PARTUUID=([0-9a-fA-F-]+)', read('CMDLINE.TXT'))
        if token:
            matches = [p for p in partitions if p['partuuid'].lower().startswith(token[1].lower())]
            result['root_argument_prefix'] = token[1]
            result['root_argument_matches'] = [p['name'] for p in matches]
            result['root_argument_selects_rootfs_uniquely'] = len(matches) == 1 and matches[0]['name'] == 'rootfs'
    return result


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('directory', type=Path)
    args = p.parse_args()
    print(json.dumps(summarize(args.directory), ensure_ascii=False, indent=2))
