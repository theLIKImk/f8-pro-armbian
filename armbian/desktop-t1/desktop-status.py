"""Optional test status launcher; no charger settings or private network data."""
import json,time
from pathlib import Path
while True:
    print('\033[2J\033[H',end='')
    print('F8 RK3588S PAD — Armbian desktop T1\n')
    try:
        data=json.loads(Path('/run/f8/power-current.json').read_text())
        cw=data['devices']['0x62']['decoded'];bq=data['devices']['0x6a']['decoded']
        print('Battery estimate: %.1f%%   %.3f V'%(cw['soc_raw_percent'],cw['voltage_mv_reference_formula']/1000))
        print('External input:',bool(bq.get('power_good')))
        print('Charge ADC estimate (mA):',bq.get('battery_charge_current_ma_estimate'))
        print('Fresh ADC sample:',data.get('adc_refresh',{}).get('fresh',False))
        print('\nCurrent and percentage are estimates; charging management remains under test.')
    except (OSError,ValueError,KeyError):print('Waiting for telemetry...')
    print('\nDesktop settings are temporary in this test edition. SSH remains available.')
    print('Close this window to return to the desktop.')
    time.sleep(3)
