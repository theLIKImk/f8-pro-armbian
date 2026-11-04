"""Read-only FIT/header/memory audit. Does not choose addresses or build a boot image."""
import hashlib
import json
from pathlib import Path
import re
import struct

from inspect_images import fdt

P = Path(__file__).resolve().parents[1]
V = P / 'vendor/ubuntu-5.10.160'
baseline = json.loads((V / 'manifest.json').read_text(encoding='utf-8'))
memory = json.loads((P / 'analysis/armbian/live-memory-baseline.json').read_text(encoding='utf-8'))
banks = [(int(row['base'], 16), int(row['size'], 16)) for row in memory['banks']]
assert all(size > 0 for _, size in banks)
assert all(a + size <= b for (a, size), (b, _) in zip(banks, banks[1:]))


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


for item in baseline['boot_assets']:
    assert digest(V / item['file']) == item['sha256'], item['name']
boot = (V / 'boot-assets/boot.img').read_bytes()
tree = fdt(boot)
payloads = []
for path, properties in tree.items():
    if not path.startswith('/images/') or path.count('/') != 2:
        continue
    size = int.from_bytes(properties['data-size'], 'big')
    offset = int.from_bytes(properties['data-position'], 'big')
    assert offset + size <= len(boot)
    data = boot[offset:offset + size]
    checksum = tree[path + '/hash']
    assert checksum['algo'] == b'sha256\0'
    assert hashlib.sha256(data).digest() == checksum['value']
    item = {'name': path.rsplit('/', 1)[1], 'offset': offset, 'bytes': size, 'sha256': checksum['value'].hex()}
    for field in ['load', 'entry']:
        if field in properties:
            value = int.from_bytes(properties[field], 'big')
            item[field] = hex(value)
            item[field + '_literal_payload_range_in_observed_ram'] = any(
                start <= value and value + size <= start + length for start, length in banks)
    payloads.append(item)


def image_header(path):
    with path.open('rb') as stream:
        header = stream.read(64)
    assert header[56:60] == b'ARM\x64'
    text_offset, runtime_size, flags = struct.unpack_from('<QQQ', header, 8)
    assert runtime_size >= path.stat().st_size
    return {'file_bytes': path.stat().st_size, 'text_offset': hex(text_offset),
            'runtime_image_bytes': runtime_size, 'flags': hex(flags), 'sha256': digest(path)}


vendor_dtb = fdt((V / 'boot-assets/board.dtb').read_bytes())
candidate = P / 'analysis/armbian/dt-validation/f8-pro-compile-check.DO-NOT-FLASH.dtb'
candidate_dtb = fdt(candidate.read_bytes())


def dynamic_nodes(nodes):
    dram = []
    placeholders = []
    for path, props in nodes.items():
        if props.get('device_type') == b'memory\0':
            dram.append({'path': path, 'reg_present': 'reg' in props})
        if path.startswith('/reserved-memory/') and path.count('/') == 2 and 'reg' in props:
            cells = props['reg']
            assert len(cells) % 16 == 0
            for index in range(0, len(cells), 16):
                start, size = struct.unpack_from('>QQ', cells, index)
                if not size:
                    placeholders.append({'path': path, 'base': hex(start), 'size': 0})
    return {'dram_nodes': dram, 'zero_size_reserved_placeholders': placeholders}


uboot = (V / 'boot-assets/uboot.img').read_bytes()
banners = sorted(set(match.decode('ascii') for match in re.findall(rb'U-Boot [0-9]{4}\.[0-9]{2}[ -~]{0,100}', uboot)))
embedded = {}
for entry in uboot.split(b'\0'):
    match = re.fullmatch(rb'(kernel_addr_r|fdt_addr_r|ramdisk_addr_r)=(0x[0-9a-fA-F]+)', entry)
    if match:
        name, value = match[1].decode(), int(match[2], 16)
        if name in embedded:
            assert embedded[name] == value
        embedded[name] = value
control_candidates = []
offset = 0
while True:
    offset = uboot.find(b'\xd0\x0d\xfe\xed', offset)
    if offset < 0:
        break
    start = offset
    offset += 4
    try:
        fields = struct.unpack_from('>10I', uboot, start)
        total, structure, strings = fields[1:4]
        assert total >= 40 and start + total <= len(uboot)
        assert structure + fields[9] <= total and strings + fields[8] <= total
        content = uboot[start:start + total]
        nodes = fdt(content)
        keys = []
        for path, properties in nodes.items():
            if path.startswith('/signature/') and path.count('/') == 2:
                keys.append({'path': path,
                             'algo': properties.get('algo', b'').rstrip(b'\0').decode('ascii'),
                             'required': properties.get('required', b'').rstrip(b'\0').decode('ascii') or None})
        control_candidates.append({'offset': start, 'bytes': total, 'sha256': hashlib.sha256(content).hexdigest(),
                                   'signature_key_nodes': keys})
    except (AssertionError, ValueError, IndexError, struct.error, UnicodeError):
        continue
manifest = json.loads((P / 'outputs/armbian/evaluation-custom-set.json').read_text())
original_header = image_header(V / 'boot-assets/Image')
custom_header = image_header(P / 'outputs/armbian/evaluation-kernel/Image')
report = {'scope': 'Archived-input integrity and static contract audit only; no loader execution or boot validation',
          'factory_fit_payloads': payloads, 'factory_fit_hashes_verified': True,
          'factory_signature_node_present': '/configurations/conf/signature' in tree,
          'signature_verification_performed': False,
          'original_image_header': original_header, 'custom_image_header': custom_header,
          'observed_dram_banks': memory['banks'], 'observed_bank_total_bytes': sum(size for _, size in banks),
          'memory_evidence_date': memory['date'], 'vendor_dtb': dynamic_nodes(vendor_dtb),
          'vendor_root_identity': {key: vendor_dtb['/'][key].rstrip(b'\0').decode('utf-8').split('\0') for key in ['model', 'compatible']},
          'candidate_root_identity': {key: candidate_dtb['/'][key].rstrip(b'\0').decode('utf-8').split('\0') for key in ['model', 'compatible']},
          'candidate_dtb': dynamic_nodes(candidate_dtb), 'candidate_dtb_sha256': digest(candidate),
          'uboot_banner_strings': banners,
          'embedded_default_address_variables': {key: hex(value) for key, value in embedded.items()},
          'embedded_defaults_are_runtime_observations': False,
          'embedded_fdt_candidates': control_candidates,
          'actual_control_fdt_selection_verified': False,
          'raw_kernel_initramfs_bytes': manifest['raw_kernel_plus_initramfs_bytes'],
          'literal_fit_load_addresses_validated': False,
          'candidate_fit_generated': False, 'boot_ready': False,
          'required_evidence': ['Loader interpretation of factory 0xffffff00/01/02 values',
                                'Runtime placement of custom kernel, initramfs and DT with non-overlap',
                                'Loader DRAM and reserved-memory fixups applied to the new DT',
                                'Complete board compatible/DT and bootargs policy',
                                'Actual candidate boot acceptance; prior 5.10 test is not 6.1 validation']}
out = P / 'analysis/armbian/loader-contract.json'
out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps(report, ensure_ascii=False, indent=2))
