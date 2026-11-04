"""Run one native makepkg process group with a timeout and thermal logging."""
import argparse
import csv
import os
from pathlib import Path
import signal
import subprocess
import time


def temperatures():
    values = []
    for path in sorted(Path('/sys/class/thermal').glob('thermal_zone*/temp')):
        value = int(path.read_text().strip())
        if not 0 < value < 200000:
            raise RuntimeError('Invalid temperature: '+str(path))
        values.append((path.parent.name, value))
    if not values:
        raise RuntimeError('Thermal sensors unavailable')
    return values


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--timeout', type=int, required=True)
    parser.add_argument('--resume', action='store_true')
    args = parser.parse_args()
    assert os.getuid() != 0 and 60 <= args.timeout <= 3000
    values = temperatures()
    if max(v for _, v in values) >= 70000:
        print('F8_THERMAL_DEFER start temperature >=70C', values, flush=True)
        return 75
    interrupted = []
    for sig in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
        signal.signal(sig, lambda number, frame: interrupted.append(number))
    command = ['makepkg', '--noconfirm', '--log']
    if args.resume:
        command.append('--noextract')
    started = time.monotonic()
    process = subprocess.Popen(command, start_new_session=True)
    reason = None
    try:
        with Path('thermal-history.csv').open('a', newline='') as stream:
            writer = csv.writer(stream)
            while process.poll() is None:
                values = temperatures()
                peak = max(v for _, v in values)
                writer.writerow([int(time.time()), round(time.monotonic()-started, 1), peak,
                                 ';'.join(f'{name}={value}' for name, value in values)])
                stream.flush()
                if interrupted:
                    reason = 128+interrupted[0]
                elif peak >= 82000:
                    print('F8_THERMAL_STOP temperature >=82C', values, flush=True)
                    reason = 75
                elif time.monotonic()-started >= args.timeout:
                    print('F8_BUILD_TIMEOUT', flush=True)
                    reason = 124
                if reason is not None:
                    break
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    pass
    finally:
        # The process group is unique to this build; never signal other builds.
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        try:
            process.wait(timeout=20)
        except subprocess.TimeoutExpired:
            pass
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        process.wait()
    return reason if reason is not None else process.returncode


if __name__ == '__main__':
    raise SystemExit(main())
