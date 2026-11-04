import json, subprocess

# C4 取帧记录里有前摄 CIF 直出成功的节点号：
d = json.load(open('/mnt/d/Netdisk/杂项/F8-PRO/archlinux/local/hardware/camera-c4-front-raw01.json'))
print(json.dumps(d, ensure_ascii=False, indent=1)[:1200])
