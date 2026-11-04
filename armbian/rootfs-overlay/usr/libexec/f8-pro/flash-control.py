#!/usr/bin/python3
"""Fixed-purpose privileged F8 LED session. EOF turns the light off."""
import fcntl,os,re,sys
from pathlib import Path

def command(line):
 parts=line.split()
 if parts in [['off'],['keepalive']]:return parts[0]
 if len(parts)==2 and parts[0] in ['pulse','steady'] and re.fullmatch(r'[0-9]{1,3}',parts[1]):
  if 1<=int(parts[1])<=100:return ' '.join(parts)
 if len(parts)==4 and parts[0]=='blink' and all(re.fullmatch(r'[0-9]{1,4}',n) for n in parts[1:]):
  if 1<=int(parts[1])<=100 and all(100<=int(n)<=5000 for n in parts[2:]):return ' '.join(parts)
 raise ValueError('Invalid flash command')

def main():
 if os.geteuid()!=0:raise SystemExit('Administrator authorization required')
 if not Path('/proc/device-tree/model').read_bytes().startswith(b'F8-PRO'):raise SystemExit('Unsupported device')
 root=Path('/sys/devices/platform/f8-flash');control=root/'control'
 led=Path('/sys/class/leds/f8:white:flash')
 if not str(led.resolve()).startswith(str(root)+'/') or (led/'max_brightness').read_text().strip()!='100':raise SystemExit('F2 flash driver unavailable')
 if sys.argv[1:]==['--session']:
  # A second panel cannot interrupt or maintain another panel's session.
  lock=Path('/run/lock/f8-flash-session.lock').open('a')
  try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  except BlockingIOError:raise SystemExit('Another flash session is active')
  try:
   print('ready',flush=True)
   while True:
    line=sys.stdin.buffer.readline(257)
    if not line:break
    if len(line)>256 or not line.endswith(b'\n'):raise ValueError('Invalid request')
    value=command(line.decode('ascii').strip())
    control.write_text(value+'\n')
    if value!='keepalive':print('ok',flush=True)
  finally:
   try:control.write_text('off\n')
   except OSError:pass
 else:
  value='pulse 100' if sys.argv[1:]==['pulse'] else command(' '.join(sys.argv[1:]))
  control.write_text(value+'\n');print('ok')

if __name__=='__main__':main()
