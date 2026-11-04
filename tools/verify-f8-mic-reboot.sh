#!/bin/sh
export XDG_RUNTIME_DIR=/run/user/1601
echo "BOOT_ID=$(cat /proc/sys/kernel/random/boot_id)"
uptime
systemctl is-system-running
echo "=== 麦克风 source（重启后） ==="
timeout 10 pw-cli ls Node 2>&1 | grep 'node.name' | grep -i 'alsa_input' || echo NO_SOURCE
echo "=== wpctl ==="
wpctl status 2>/dev/null | sed -n '/Sources/,/Filters/p' | head -6
echo "=== 捕获增益（asound.state 恢复验证） ==="
amixer -c 0 sget 'Left Channel' 2>/dev/null | grep Mono
amixer -c 0 sget 'ALC Capture Function' 2>/dev/null | grep Item0
amixer -c 0 sget 'Capture Digital' 2>/dev/null | grep 'Front Left'
echo "=== UCM/WP 配置文件仍在 ==="
sudo -n ls /usr/share/wireplumber/wireplumber.conf.d/50-f8-ucm.conf /usr/share/alsa/ucm2/F8-PRO/HiFi.conf 2>&1
echo "=== 录 8 秒验证（请说话） ==="
timeout 12 arecord -D hw:0,0 -f S16_LE -r 48000 -c 2 -d 6 /tmp/f8-reboot-mic.wav 2>&1 | tail -1
python3 - <<'PY'
import wave, struct
w = wave.open('/tmp/f8-reboot-mic.wav')
n = w.getnframes(); data = w.readframes(n)
s = struct.unpack('<%dh' % (len(data)//2), data)
seg = len(s)//6
for i in range(6):
    c = s[i*seg:(i+1)*seg]
    print('seg%d rms %.0f' % (i, (sum(x*x for x in c)/len(c))**0.5))
print('peak', max(abs(x) for x in s))
PY
rm -f /tmp/f8-reboot-mic.wav
echo DONE
