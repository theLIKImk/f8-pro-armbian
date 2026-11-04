#!/bin/sh
# 这份 console-ramoops 是**上次正常关机**的记录（reboot: Power down），
# 不是 PM1 panic。PM1 失败可能发生在极早期（loader 阶段或 kernel 刚起），
# ramoops 没留下新记录（或者被这次成功启动覆盖了一部分）。
# 换个角度：看 ramoops 有几个分区、时间戳：
sudo -n ls -la /sys/fs/pstore/
for f in /sys/fs/pstore/*; do
  echo "== $f"
  sudo -n head -3 "$f" 2>/dev/null
done
echo DONE
