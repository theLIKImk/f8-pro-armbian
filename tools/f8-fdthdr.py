import struct
data = open('/tmp/c2.fdt','rb').read()
v = struct.unpack('>10I', data[:40])
print([hex(x) for x in v])
