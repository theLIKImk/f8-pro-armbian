data = open('/tmp/f8-front-b.raw','rb').read()
y = data[:640*480]
avg = sum(y)/len(y)
print('Y avg=%.1f min=%d max=%d' % (avg, min(y), max(y)))
if avg < 40:
    print('judge: TOO_DARK')
elif avg > 220:
    print('judge: TOO_BRIGHT')
else:
    print('judge: ACCEPTABLE')
