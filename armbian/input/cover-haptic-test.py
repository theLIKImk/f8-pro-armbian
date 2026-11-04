#!/usr/bin/python3
import json,os,sys,time
from pathlib import Path
from PyQt6.QtCore import QProcess,QTimer,Qt
from PyQt6.QtWidgets import QApplication,QCheckBox,QLabel,QPushButton,QVBoxLayout,QWidget
class Window(QWidget):
 def __init__(self):
  super().__init__();self.setWindowTitle('F8 霍尔与振动测试');self.resize(620,360)
  self.config=Path.home()/'.config/f8-cover.json';self.label=QLabel();self.label.setAlignment(Qt.AlignmentFlag.AlignCenter);self.label.setStyleSheet('font-size:28px;padding:22px')
  self.info=QLabel();self.info.setWordWrap(True);self.result=QLabel('振动为短脉冲，不随亮度变化。');self.result.setWordWrap(True)
  self.option=QCheckBox('合盖熄屏 / 开盖亮屏');self.option.toggled.connect(self.configure)
  button=QPushButton('短振测试（80 毫秒）');button.clicked.connect(self.vibrate)
  self.process=QProcess(self);self.process.finished.connect(self.finished)
  layout=QVBoxLayout(self)
  for w in [self.label,self.info,self.option,button,self.result]:layout.addWidget(w)
  self.timer=QTimer(self);self.timer.timeout.connect(self.refresh);self.timer.start(200);self.refresh()
 def refresh(self):
  try:
   raw=Path('/sys/devices/platform/f8-cover-haptic/hall_raw').read_text().strip();s=json.loads((Path.home()/'.cache/f8-cover/status.json').read_text());c=json.loads(self.config.read_text())
   self.label.setText('保护盖：合上' if raw=='0' else '保护盖：打开')
   self.info.setText('开合事件：'+str(s['events_count'])+'\n'+('合盖行为已启用' if s['screen_enabled'] else '仅观察，不改变屏幕')+('\n'+s['error'] if s['error'] else ''))
   self.option.blockSignals(True);self.option.setChecked(c.get('screen_enabled',False));self.option.setEnabled(c.get('validated',False));self.option.blockSignals(False)
  except (OSError,ValueError,KeyError):self.label.setText('正在等待驱动／观察服务…')
 def configure(self,value):
  c=json.loads(self.config.read_text());c['screen_enabled']=value;self.config.write_text(json.dumps(c))
 def vibrate(self):
  if self.process.state()!=QProcess.ProcessState.NotRunning:return
  self.result.setText('短振测试中…');self.process.start('/usr/local/bin/f8-vibrate',['--milliseconds','80'])
 def finished(self,code,status):
  self.result.setText('短振指令完成' if code==0 else '短振失败：'+bytes(self.process.readAllStandardError()).decode(errors='replace'))
app=QApplication(sys.argv[:1]);window=Window();window.show();app.exec()
