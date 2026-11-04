import re
o = open('/tmp/orig.dts').read()
mo = re.search(r'\tmipi2-csi2 \{.*?\n\t\};', o, re.S)
print('orig mipi2 data-lanes:', re.findall(r'data-lanes = <[^>]+>', mo.group(0)) if mo else 'NO BLOCK')
m2 = re.search(r'\tcsi2-dphy1 \{.*?\n\t\};', o, re.S)
print('orig dphy1 found:', bool(m2))
if m2:
    print('orig dphy1 data-lanes:', re.findall(r'data-lanes = <[^>]+>', m2.group(0)))
    st = re.findall(r'status = "([^"]+)"', m2.group(0))
    print('orig dphy1 status:', st)
# 原厂 gc5035：
m3 = re.search(r'gc5035@\w+ \{.*?\n\t\t\};', o, re.S)
print('orig gc5035 found:', bool(m3))
if m3:
    blk = m3.group(0)
    print('orig gc5035 data-lanes:', re.findall(r'data-lanes = <[^>]+>', blk))
    print('orig gc5035 remote:', re.findall(r'remote-endpoint = <[^>]+>', blk))
    print('--- head 600 ---')
    print(blk[:600])
