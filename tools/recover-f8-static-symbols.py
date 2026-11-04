"""Decode archived kallsyms and independently anchor offsets using the ARM64 entry branch."""
from collections import Counter
import hashlib
import importlib.metadata
import json
import logging
from pathlib import Path
import struct
import sys

P = Path(__file__).resolve().parents[1]
LIB = P / 'tools/vendor-lib/vmlinux-to-elf-1.4.0'
sys.path.insert(0, str(LIB))
from vmlinux_to_elf.core.kallsyms import KallsymsFinder

OUT = P / 'analysis/armbian/touch-static'
OUT.mkdir(parents=True, exist_ok=True)
logging.basicConfig(filename=OUT / 'decode.log', level=logging.INFO, encoding='utf-8')
original = (P / 'vendor/ubuntu-5.10.160/boot-assets/Image').read_bytes()
assert hashlib.sha256(original).hexdigest() == '90d648c1e4e47ce6b4a83415694fa9b4a7283465fa3749297d2078abb20bffa2'
finder = KallsymsFinder(original, bit_size=64)
base = finder.kernel_text_candidate
symbols = [{'name': symbol.name, 'type': symbol.symbol_type.value,
            'link_address': symbol.virtual_address, 'file_offset': symbol.virtual_address - base}
           for symbol in finder.symbols]
reference = next(item for item in symbols if item['name'] == '_stext')['link_address']
live = json.loads((P / 'analysis/armbian/touch-symbol-offsets.json').read_text())
assert live['reference_symbol'] == '_stext'
decoded = Counter((item['name'], item['link_address'] - reference) for item in symbols)
assert all(decoded[(item['name'], item['reference_relative_offset'])] > 0 for item in live['symbols'])
anchors = []
for offset in [0, 4]:
    instruction = struct.unpack_from('<I', original, offset)[0]
    if instruction & 0xfc000000 == 0x14000000:
        immediate = instruction & 0x3ffffff
        if immediate & (1 << 25):
            immediate -= 1 << 26
        target = offset + immediate * 4
        names = [item['name'] for item in symbols if item['file_offset'] == target]
        anchors.append({'header_instruction_offset': offset, 'target_file_offset': target, 'decoded_target_symbols': names})
assert any(set(item['decoded_target_symbols']) & {'primary_entry', 'stext', '_stext'} for item in anchors), anchors
gsl = [item for item in symbols if 'gsl' in item['name'].lower() or item['name'] == 'report_data']
(OUT / 'all-symbols.json').write_text(json.dumps(symbols) + '\n')
# Relocations are applied by the decoder only to a separate analysis copy.
(OUT / 'relocated-ANALYSIS-ONLY.bin').write_bytes(finder.kernel_img)
report = {'scope': 'Archived Image decoding and read-only live symbol-relative corroboration; not controller firmware execution',
          'tool_version': importlib.metadata.version('vmlinux-to-elf'),
          'peewee_version': importlib.metadata.version('peewee'),
          'decoder_sha256': hashlib.sha256((LIB / 'vmlinux_to_elf/core/kallsyms.py').read_bytes()).hexdigest(),
          'decoded_symbol_count': len(symbols), 'live_relative_symbols_matched': len(live['symbols']),
          'arm64_header_branch_anchors': anchors, 'image_base_anchor_verified': True,
          'static_link_base': base, 'stext_file_offset': reference - base, 'gsl_symbols': gsl,
          'relocation_table_file_range': [finder.elf64_rela_start, finder.elf64_rela_end_excl],
          'raw_runtime_addresses_saved': False, 'original_image_modified': False}
(OUT / 'recovery.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({'decoded_symbol_count': len(symbols), 'live_relative_symbols_matched': len(live['symbols']),
                  'image_base_anchor_verified': True, 'stext_file_offset': reference - base, 'gsl_symbols': gsl}, indent=2))
