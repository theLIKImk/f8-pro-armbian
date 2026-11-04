"""Read-only upstream audit; save commit-pinned evidence without building/flashing."""
import concurrent.futures
import hashlib
import json
from pathlib import Path
import urllib.error
import urllib.request

BASE = Path(__file__).resolve().parents[1]
OUT = BASE / 'analysis/armbian/source-audit'


def get(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'F8-PRO-porting-audit'})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    refs = [('build', 'main'), ('linux-rockchip', 'rk-6.1-rkr7.2')]
    pins = {}
    for repo, ref in refs:
        data = get(f'https://api.github.com/repos/armbian/{repo}/commits/{ref}')
        obj = json.loads(data)
        pins[repo] = obj['sha']
        (OUT / f'{repo}-commit.json').write_bytes(data)
    paths = {
        'build': ['config/sources/families/rockchip-rk3588.conf',
                  'config/sources/families/include/rockchip_vendor_common.inc',
                  'config/kernel/linux-rk35xx-vendor.config'],
        'linux-rockchip': ['drivers/gpu/drm/panthor/Kconfig',
            'drivers/input/touchscreen/Kconfig', 'drivers/input/touchscreen/Makefile',
            'drivers/input/touchscreen/gslx680_pad.c',
            'drivers/input/sensors/accel/mpu6500_acc.c',
            'drivers/input/sensors/compass/ak8963.c',
            'drivers/input/sensors/gyro/mpu6500_gyro.c',
            'drivers/power/supply/Kconfig',
            'drivers/gpu/drm/panel/panel-simple.c',
            'sound/soc/codecs/es8323.c', 'sound/soc/codecs/es8388.c',
            'sound/soc/rockchip/rockchip_multicodecs.c',
            'drivers/media/i2c/gc5035.c', 'drivers/media/i2c/ov8858.c',
            'drivers/power/supply/cw2015_battery.c',
            'drivers/power/supply/bq25890_charger.c',
            'drivers/iio/imu/inv_mpu6050/inv_mpu_i2c.c',
            'drivers/iio/magnetometer/ak8975.c',
            'arch/arm64/boot/dts/rockchip/Makefile']}

    def fetch(item):
        repo, path = item
        url = f'https://raw.githubusercontent.com/armbian/{repo}/{pins[repo]}/{path}'
        record = {'repository': repo, 'commit': pins[repo], 'path': path, 'url': url}
        try:
            data = get(url)
            dst = OUT / repo / path
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_bytes(data)
            record.update(status='present', sha256=hashlib.sha256(data).hexdigest(), bytes=len(data))
        except urllib.error.HTTPError as e:
            record.update(status='path_not_found' if e.code == 404 else 'http_error', code=e.code)
        except Exception as e:
            record.update(status='fetch_error', error=str(e))
        return record

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        records = list(pool.map(fetch, [(r, p) for r, ps in paths.items() for p in ps]))
    result = {'queried_date': '2026-10-28', 'pins': pins,
              'scope': 'Path presence only; 404 is not proof the driver is absent elsewhere. No build or hardware validation.',
              'files': records}
    (OUT / 'manifest.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
