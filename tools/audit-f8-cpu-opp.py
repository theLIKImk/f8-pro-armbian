"""Compare vendor/candidate CPU OPP tables without changing clocks or voltages."""
import hashlib
import json
from pathlib import Path
import subprocess

P = Path(__file__).resolve().parents[1]
vendor = P / 'vendor/ubuntu-5.10.160/boot-assets/board.dtb'
candidate = P / 'analysis/armbian/dt-validation/f8-pro-compile-check.DO-NOT-FLASH.dtb'


def properties(dtb, node):
    keys = subprocess.check_output(['fdtget', '-p', str(dtb), node], text=True).splitlines()
    result = {}
    for key in keys:
        kind = 's' if key in ['compatible', 'nvmem-cell-names', 'rockchip,pvtm-thermal-zone'] else 'x'
        value = subprocess.check_output(['fdtget', '-t', kind, str(dtb), node, key], text=True).strip()
        result[key] = value if kind == 's' else [int(cell, 16) for cell in value.split()]
    return result


def children(dtb, node):
    return subprocess.check_output(['fdtget', '-l', str(dtb), node], text=True).splitlines()


def table(dtb, node):
    return {'properties': properties(dtb, node),
            'opps': {child: properties(dtb, node + '/' + child) for child in children(dtb, node)}}


def calibration_cells(dtb, contents):
    nodes = {}
    for child in children(dtb, '/otp@fecc0000'):
        node = '/otp@fecc0000/' + child
        fields = properties(dtb, node)
        if 'phandle' in fields:
            nodes[fields['phandle'][0]] = {'path': node, 'reg': fields.get('reg'), 'bits': fields.get('bits')}
    names = contents['properties']['nvmem-cell-names'].split()
    references = contents['properties']['nvmem-cells']
    assert len(names) == len(references)
    return {name: nodes[reference] for name, reference in zip(names, references)}


clusters = []
for index, cpu, rail in [(0, 'cpu@0', '/spi@feb20000/rk806single@0/regulators/DCDC_REG2'),
                         (1, 'cpu@400', '/i2c@fd880000/rk8602@42'),
                         (2, 'cpu@600', '/i2c@fd880000/rk8603@43')]:
    path = f'/cluster{index}-opp-table'
    old, new = table(vendor, path), table(candidate, path)
    old_cells, new_cells = calibration_cells(vendor, old), calibration_cells(candidate, new)
    for name, cell in old_cells.items():
        assert new_cells[name]['reg'] == cell['reg'] and new_cells[name]['bits'] == cell['bits'], (path, name)
    # Check CPU-to-table references independently in each DTB.
    for dtb, contents in [(vendor, old), (candidate, new)]:
        assert properties(dtb, '/cpus/' + cpu)['operating-points-v2'] == contents['properties']['phandle']
    regulator = properties(candidate, rail)
    low, high = regulator['regulator-min-microvolt'][0], regulator['regulator-max-microvolt'][0]
    violations, frequencies, differences = [], [], []
    for name, opp in new['opps'].items():
        cells = opp['opp-hz']
        hz = (cells[0] << 32) | cells[1]
        frequencies.append(hz)
        for key, values in opp.items():
            if not key.startswith('opp-microvolt'):
                continue
            assert len(values) == 6, (path, name, key, values)
            for supply, start in [('cpu', 0), ('mem', 3)]:
                target, minimum, maximum = values[start:start + 3]
                assert minimum <= target <= maximum
                # Max is tolerance, not a request to program it. The target
                # voltage and allowed interval must intersect the board rail.
                if not (low <= target <= high and max(low, minimum) <= min(high, maximum)):
                    violations.append({'opp': name, 'property': key, 'supply': supply,
                                       'target': target, 'range': [minimum, maximum]})
        if name in old['opps'] and old['opps'][name] != opp:
            changed = sorted(key for key in set(old['opps'][name]) | set(opp)
                             if old['opps'][name].get(key) != opp.get(key))
            differences.append({'opp': name, 'changed_properties': changed})
    ignored = {'phandle', 'nvmem-cells', 'rockchip,grf', 'rockchip,dsu-grf'}
    changes = {key: {'vendor': old['properties'].get(key), 'candidate': new['properties'].get(key)}
               for key in sorted(set(old['properties']) | set(new['properties']))
               if key not in ignored and old['properties'].get(key) != new['properties'].get(key)}
    clusters.append({'table': path, 'cpu': cpu, 'rail': rail, 'rail_range_uv': [low, high],
                     'vendor_opp_count': len(old['opps']), 'candidate_opp_count': len(new['opps']),
                     'candidate_frequency_range_hz': [min(frequencies), max(frequencies)],
                     'added_opps': sorted(set(new['opps']) - set(old['opps'])),
                     'removed_opps': sorted(set(old['opps']) - set(new['opps'])),
                     'changed_common_opps': differences, 'table_property_changes': changes,
                     'vendor_calibration_cells': old_cells, 'candidate_calibration_cells': new_cells,
                     'shared_calibration_cell_offsets_verified': True,
                     'voltage_constraint_violations': violations})
report = {'scope': 'Static DT audit only; all bins/voltage variants, no runtime bin selection or DVFS validation',
          'candidate_sha256': hashlib.sha256(candidate.read_bytes()).hexdigest(),
          'reference_properties_excluded_from_numeric_comparison': sorted(ignored),
          'clusters': clusters}
out = P / 'analysis/armbian/cpu-opp-audit.json'
out.write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps([{'table': c['table'], 'opps': c['candidate_opp_count'],
                   'property_changes': len(c['table_property_changes']),
                   'voltage_violations': len(c['voltage_constraint_violations'])} for c in clusters]))
