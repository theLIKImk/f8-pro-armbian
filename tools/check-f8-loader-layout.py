"""Check embedded-default placement geometry; never selects or applies addresses."""
import copy
import json
from pathlib import Path

P = Path(__file__).resolve().parents[1]
MIB = 1024 ** 2
GIB = 1024 ** 3


def validate(layout):
    errors = []
    banks = layout['banks']
    regions = layout['regions']
    kernel, initrd, dtb = (regions[name] for name in ['kernel', 'initramfs', 'fdt'])
    base = kernel['address'] - layout['text_offset']
    if base < 0 or base % (2 * MIB):
        errors.append('kernel-base-not-2MiB-aligned')
    if dtb['address'] % 8 or dtb['size'] > 2 * MIB:
        errors.append('fdt-alignment-or-size')
    for name, region in regions.items():
        address, size = region['address'], region['size']
        if address < 0 or size <= 0 or address + size > 1 << 48:
            errors.append(name + '-invalid-range')
        if not any(start <= address and address + size <= start + length for start, length in banks):
            errors.append(name + '-outside-described-dram-bank')
        for reserved in layout['reserved']:
            if address < reserved['address'] + reserved['size'] and reserved['address'] < address + size:
                errors.append(name + '-overlaps-reserved-memory')
    names = list(regions)
    for index, name in enumerate(names):
        a = regions[name]
        for other in names[index + 1:]:
            b = regions[other]
            if a['address'] < b['address'] + b['size'] and b['address'] < a['address'] + a['size']:
                errors.append(name + '-overlaps-' + other)
    window_start = min(kernel['address'], initrd['address']) // GIB * GIB
    window_end = max(kernel['address'] + kernel['size'], initrd['address'] + initrd['size'])
    if window_end - window_start > 32 * GIB:
        errors.append('kernel-initramfs-exceeds-32GiB-aligned-window')
    return errors


base = {'banks': [(2 * MIB, 200 * MIB)], 'text_offset': 0, 'reserved': [],
        'regions': {'kernel': {'address': 4 * MIB, 'size': 40 * MIB},
                    'initramfs': {'address': 64 * MIB, 'size': 3 * MIB},
                    'fdt': {'address': 80 * MIB, 'size': 200000}}}
tests = []
assert validate(base) == []
tests.append({'name': 'synthetic-valid', 'passed': True})
for name, change, expected in [
    ('kernel-unaligned', lambda x: x['regions']['kernel'].update(address=4 * MIB + 8), 'kernel-base-not-2MiB-aligned'),
    ('runtime-kernel-overlap', lambda x: x['regions']['initramfs'].update(address=43 * MIB), 'kernel-overlaps-initramfs'),
    ('bank-hole', lambda x: x['regions']['initramfs'].update(address=300 * MIB), 'initramfs-outside-described-dram-bank'),
    ('reserved-overlap', lambda x: x['reserved'].append({'address': 64 * MIB, 'size': MIB}), 'initramfs-overlaps-reserved-memory'),
    ('fdt-unaligned', lambda x: x['regions']['fdt'].update(address=80 * MIB + 4), 'fdt-alignment-or-size'),
    ('fdt-too-large', lambda x: x['regions']['fdt'].update(size=2 * MIB + 1), 'fdt-alignment-or-size'),
]:
    fixture = copy.deepcopy(base)
    change(fixture)
    assert expected in validate(fixture), name
    tests.append({'name': name, 'passed': True})
far = copy.deepcopy(base)
far['banks'].append((36 * GIB, GIB))
far['regions']['initramfs']['address'] = 36 * GIB
assert 'kernel-initramfs-exceeds-32GiB-aligned-window' in validate(far)
tests.append({'name': 'initramfs-window-too-wide', 'passed': True})

audit = json.loads((P / 'analysis/armbian/loader-contract.json').read_text(encoding='utf-8'))
init = json.loads((P / 'analysis/armbian/initramfs/custom/verified-initramfs.json').read_text())
variables = audit['embedded_default_address_variables']
assert set(variables) == {'kernel_addr_r', 'fdt_addr_r', 'ramdisk_addr_r'}
candidate = P / 'analysis/armbian/dt-validation/f8-pro-compile-check.DO-NOT-FLASH.dtb'
old_memory = json.loads((P / 'analysis/armbian/live-memory-baseline.json').read_text())
old_vendor_storage = old_memory['loader_fixed_vendor_storage']
layout = {'banks': [(int(item['base'], 16), int(item['size'], 16)) for item in audit['observed_dram_banks']],
          'text_offset': int(audit['custom_image_header']['text_offset'], 16),
          'reserved': [{'address': int(old_vendor_storage['base'], 16), 'size': int(old_vendor_storage['size'], 16)}],
          'regions': {
              'kernel': {'address': int(variables['kernel_addr_r'], 16), 'size': audit['custom_image_header']['runtime_image_bytes']},
              'initramfs': {'address': int(variables['ramdisk_addr_r'], 16), 'size': init['archive_bytes']},
              'fdt': {'address': int(variables['fdt_addr_r'], 16), 'size': candidate.stat().st_size}}}
errors = validate(layout)
handoff = json.loads((P / 'analysis/armbian/loader-placeholder/verified-handoff-paths.json').read_text())
padding = handoff['dt_expansion_bytes']
assert padding == 0x3000
padded_layout = copy.deepcopy(layout)
padded_layout['regions']['fdt']['size'] += padding
padded_errors = validate(padded_layout)
fixture = copy.deepcopy(base)
fixture['regions']['fdt'] = {'address': 202 * MIB - 65536, 'size': 60000}
assert validate(fixture) == []
fixture['regions']['fdt']['size'] += padding
assert 'fdt-outside-described-dram-bank' in validate(fixture)
tests.append({'name': 'fdt-padding-crosses-bank-end', 'passed': True})
report = {'scope': 'Geometry screening using embedded defaults and OLD observed banks, not a measured handoff',
          'synthetic_tests': tests, 'embedded_default_geometry_errors': errors, 'layout_screened': layout,
          'archived_fdt_expansion_bytes': padding,
          'padded_embedded_default_geometry_errors': padded_errors,
          'padded_layout_screened': padded_layout,
          'kernel_size_includes_runtime_bss': True, 'actual_runtime_addresses_observed': False,
          'final_fixed_up_fdt_size_observed': False, 'reserved_memory_coverage_complete': False,
          'dtb_cacheability_verified': False, 'boot_ready': False}
report['new_kernel_runtime_addresses_observed'] = False
report['old_kernel_placement_metadata_file'] = 'analysis/armbian/live-loader-placement-2026-10-29.json'
(P / 'analysis/armbian/loader-layout-check.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
