#!/bin/sh
# Sources 为空。看 card 的可用 profile（输出被截断了，用完整 JSON）：
pactl -f json list cards 2>/dev/null | python3 -c "
import json,sys
cards = json.load(sys.stdin)
for c in cards:
    for p in c.get('profiles', []):
        print(p.get('name'), '|', p.get('description'), '| available:', p.get('available'))
    print('ACTIVE:', c.get('active_profile'))
"
echo DONE
