"""Console status page on tty2; tty1 remains available for the Wayland trial."""
import fcntl
import json
import os
from pathlib import Path
import shutil
import signal
import socket
import struct
import subprocess
import time

alive=True
def stop(*args):
    global alive
    alive=False
signal.signal(signal.SIGTERM,stop)

def ip_address():
    try:
        routes=Path('/proc/net/route').read_text().splitlines()[1:]
        interfaces=list(dict.fromkeys(line.split()[0] for line in routes))
        with socket.socket(socket.AF_INET,socket.SOCK_DGRAM) as sock:
            for interface in interfaces:
                if interface=='lo':continue
                try:
                    data=fcntl.ioctl(sock.fileno(),0x8915,struct.pack('256s',interface.encode()[:15]))
                    address=socket.inet_ntoa(data[20:24])
                    if not address.startswith(('127.','169.254.')):return address
                except OSError:pass
    except OSError:pass
    return 'WAITING FOR WIFI'

def power_text():
    try:
        data=json.loads(Path('/run/f8/power-current.json').read_text())
        cw=data['devices']['0x62']['decoded']
        return '%.0f%%  %.3f V'%(cw['soc_raw_percent'],cw['voltage_mv_reference_formula']/1000)
    except (OSError,ValueError,KeyError):return 'READING'

def main():
    subprocess.run(['chvt','2'],check=False)
    with open('/dev/tty2','w',buffering=1) as out:
        out.write('\033[2J\033[?25l')
        tick=0
        try:
            while alive:
                columns,rows=shutil.get_terminal_size((100,60))
                # Query the actual status VT instead of the service's pipe.
                try:rows,columns,_,_=struct.unpack('HHHH',fcntl.ioctl(out.fileno(),0x5413,b'\0'*8))
                except OSError:pass
                columns=max(40,columns);rows=max(20,rows)
                uptime=int(float(Path('/proc/uptime').read_text().split()[0]))
                if tick%10==0:
                    address=ip_address();power=power_text()
                def line(row,text):
                    left=max(1,(columns-len(text))//2+1)
                    out.write('\033[%d;1H\033[2K\033[%d;%dH%s'%(row,row,left,text))
                line(3,'[TIME] UP %02d:%02d:%02d'%(uptime//3600,uptime//60%60,uptime%60))
                line(5,'[POWER] '+power)
                line(rows//2,'F8 RK3588S PAD')
                line(rows//2+4,'[BOOT]' if tick%2==0 else '      ')
                line(rows-5,'[SSH] '+address)
                line(rows-3,'USER f8test / KEY AUTH')
                out.flush();tick+=1;time.sleep(0.5)
        finally:out.write('\033[?25h')

if __name__=='__main__':main()
