import os, glob
ok = []
fail = []
for d in sorted(glob.glob('/dev/video*')):
    try:
        fd = os.open(d, os.O_RDWR)
        os.close(fd)
        ok.append(d)
    except OSError as e:
        fail.append((d, e.errno))
print('OPENABLE:', ok)
print('FAILED:', fail)
