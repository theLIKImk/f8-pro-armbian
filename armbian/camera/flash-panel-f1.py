#!/usr/bin/python3
"""Native Qt/Wayland panel for the bounded F8 flash LED."""
import sys
from pathlib import Path
from PyQt6.QtCore import QProcess,QTimer
from PyQt6.QtWidgets import QApplication,QLabel,QPushButton,QVBoxLayout,QWidget
app=QApplication(sys.argv)
w=QWidget();w.setWindowTitle('F8 闪光灯');w.resize(480,280)
layout=QVBoxLayout(w)
intro=QLabel('后置闪光灯\n每次短亮约 0.5 秒，内核自动熄灭。\n当前支持固定短闪；尚未接入拍照同步或持续补光。');intro.setWordWrap(True);layout.addWidget(intro)
status=QLabel();layout.addWidget(status)
pulse=QPushButton('短闪测试（0.5 秒）');off=QPushButton('立即熄灭')
for b in [pulse,off]:b.setMinimumHeight(52);layout.addWidget(b)
message=QLabel('首次操作需要管理员验证。');message.setWordWrap(True);layout.addWidget(message)
proc=QProcess(w);cooldown=QTimer(w);cooldown.setSingleShot(True);cooldown.setInterval(1200)
def update():
 try:
  value=(Path('/sys/class/leds/f8:white:flash')/'brightness').read_text().strip()
  status.setText('状态：点亮中' if value=='1' else '状态：已熄灭')
  ready=True
 except OSError:status.setText('状态：闪光灯驱动未就绪');ready=False
 pulse.setEnabled(ready and proc.state()==QProcess.ProcessState.NotRunning and not cooldown.isActive())
 off.setEnabled(ready and proc.state()==QProcess.ProcessState.NotRunning)
def execute(action):
 if proc.state()!=QProcess.ProcessState.NotRunning:return
 message.setText('等待管理员验证…');proc.start('/usr/bin/pkexec',['/usr/libexec/f8-pro/flash-control.py',action]);update()
def finished(code,status):
 if code==0:message.setText('操作已完成。');cooldown.start()
 else:message.setText('未执行：验证取消、灯正在冷却或驱动未就绪。')
 update()
proc.finished.connect(finished);proc.errorOccurred.connect(lambda _:message.setText('无法启动管理员验证。'))
pulse.clicked.connect(lambda:execute('pulse'));off.clicked.connect(lambda:execute('off'))
timer=QTimer(w);timer.timeout.connect(update);timer.start(150);cooldown.timeout.connect(update)
update();w.show();sys.exit(app.exec())
