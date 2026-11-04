data = open('/tmp/f8-rear-now.raw','rb').read()
y = data[:640*480]
avg = sum(y)/len(y)
print('rear ISP Y avg=%.1f min=%d max=%d' % (avg, min(y), max(y)))
print('judge:', 'DARK' if avg < 40 else 'BRIGHT' if avg > 220 else 'OK')
# 前摄黑帧但曝光 readback=1200（说明 set 生效了）——但输出恒 16。
# ISP 输出恒黑 + sensor 出流（CIF RAW 曾成功）→ ISP 管线前摄路径的 3A/初始化问题：
# 没跑 RKAIQ 时 ISP 黑电平/增益未配置。后摄当时也是"前9帧黑、需 IQ"。
# 结论：路线 A 的"固定参数直出"在此 ISP 上不成立 —— ISP 需要至少一次配置。
# 替代：用 CIF 直出 RG10 raw（前摄曾成功）→ 软件 debayer 成 PNG，绕过 ISP。
data2 = open('/tmp/f8-front-a.raw','rb').read()
print('front-b len:', len(data2))
