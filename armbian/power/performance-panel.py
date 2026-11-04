#!/usr/bin/python3
"""Touch-friendly, non-root CPU/GPU frequency controls for the F8 tablet."""
import json,sys
from pathlib import Path
from PyQt6.QtCore import QProcess,QTimer
from PyQt6.QtWidgets import QApplication,QWidget,QVBoxLayout,QHBoxLayout,QGridLayout,QGroupBox,QLabel,QComboBox,QPushButton,QScrollArea,QProgressBar
from performance_state import DEVICES,snapshot,temperatures

class Card(QGroupBox):
 def __init__(self,key,owner):
  super().__init__(DEVICES[key][0]);self.key=key;self.owner=owner;self.loaded=False
  v=QVBoxLayout(self);self.current=QLabel('读取中');self.current.setStyleSheet('font-size:27px;font-weight:600');v.addWidget(self.current)
  self.bar=QProgressBar();self.bar.setTextVisible(False);self.bar.setMaximumHeight(9);v.addWidget(self.bar)
  self.details=QLabel();self.details.setWordWrap(True);v.addWidget(self.details)
  self.mode=QComboBox()
  for label,value in [('自动调频（全部已开放档位）','auto'),('手动范围','range'),('固定目标频率','fixed')]:self.mode.addItem(label,value)
  v.addWidget(self.mode);self.low=QComboBox();self.high=QComboBox()
  row=QHBoxLayout();row.addWidget(QLabel('最低 / 目标'));row.addWidget(self.low);row.addWidget(QLabel('最高'));row.addWidget(self.high);v.addLayout(row)
  self.apply=QPushButton('应用');self.apply.clicked.connect(self.submit);v.addWidget(self.apply)
  self.mode.currentIndexChanged.connect(self.selection);self.selection()
 def selection(self):
  mode=self.mode.currentData();self.low.setEnabled(mode!='auto');self.high.setEnabled(mode=='range')
 def submit(self):
  mode=self.mode.currentData();lo=self.low.currentData();hi=lo if mode=='fixed' else self.high.currentData()
  args=['--device',self.key,'--mode',mode]
  if mode!='auto':args+=['--minimum',str(lo),'--maximum',str(hi)]
  self.owner.execute(args)
 def refresh(self,temps):
  s=snapshot(self.key);active=s['enabled'];self.apply.setEnabled(active and not self.owner.busy)
  if not active:
   self.current.setText('尚不可调');self.details.setText(s.get('reason',''));self.bar.setValue(0);return
  scale=s['scale'];self.current.setText(f"{s['current']/scale:g} MHz")
  self.bar.setValue(round(100*s['current']/max(s['allowed'])))
  temp=temps.get('gpu-thermal' if self.key=='gpu' else 'soc-thermal')
  self.details.setText(f"当前范围 {s['minimum']/scale:g}–{s['maximum']/scale:g} MHz · {s['governor']}\n"+(f"温度 {temp:.1f}°C · " if temp is not None else '')+f"已开放最高 {s['validated_mhz']} MHz")
  if not self.loaded or self.allowed!=s['allowed']:
   self.allowed=s['allowed'];self.loaded=True
   for combo in [self.low,self.high]:
    combo.clear()
    for freq in self.allowed:combo.addItem(f'{freq/scale:g} MHz',freq)
   self.low.setCurrentIndex(max(0,self.low.findData(s['minimum'])));self.high.setCurrentIndex(max(0,self.high.findData(s['maximum'])))

class Panel(QWidget):
 def __init__(self):
  super().__init__();self.busy=False;self.setWindowTitle('F8 性能控制');self.resize(940,770)
  outer=QVBoxLayout(self);title=QLabel('性能控制');title.setStyleSheet('font-size:28px;font-weight:600');outer.addWidget(title)
  note=QLabel('型号上限：GPU 1000 MHz · A76 2400 MHz · A55 1800 MHz\n可选档位按本机启动校准结果开放；固定目标仍受系统温控限制。');note.setWordWrap(True);outer.addWidget(note)
  scroll=QScrollArea();scroll.setWidgetResizable(True);body=QWidget();grid=QGridLayout(body);self.grid=grid;self.columns=0;self.cards=[]
  for i,key in enumerate(DEVICES):
   c=Card(key,self);self.cards.append(c);grid.addWidget(c,i//2,i%2)
  scroll.setWidget(body);outer.addWidget(scroll)
  self.auto=QPushButton('全部恢复自动调频');self.auto.clicked.connect(lambda:self.execute(['--all-auto']));outer.addWidget(self.auto)
  self.enablecpu=QPushButton('启用本次 CPU 调频');self.enablecpu.clicked.connect(lambda:self.execute(['--enable-cpu']));outer.addWidget(self.enablecpu)
  self.status=QLabel('调整仅作用于本次启动；应用时会进行管理员验证。');self.status.setWordWrap(True);outer.addWidget(self.status)
  self.proc=QProcess(self);self.proc.finished.connect(self.finished);self.proc.errorOccurred.connect(self.failed)
  self.timer=QTimer(self);self.timer.timeout.connect(self.refresh);self.timer.start(1500);self.refresh()
 def resizeEvent(self,event):
  super().resizeEvent(event)
  if not hasattr(self,'cards'):return
  cols=1 if self.width()<820 else 2
  if cols==self.columns:return
  self.columns=cols
  for c in self.cards:self.grid.removeWidget(c)
  for i,c in enumerate(self.cards):self.grid.addWidget(c,i//cols,i%cols)
  self.grid.setColumnStretch(0,1);self.grid.setColumnStretch(1,1 if cols==2 else 0)
 def refresh(self):
  temps=temperatures()
  for c in self.cards:c.refresh(temps)
  self.auto.setEnabled(not self.busy)
  show=not any(snapshot(k)['enabled'] for k in ['cpu0','cpu4','cpu6'])
  self.enablecpu.setVisible(show);self.enablecpu.setEnabled(not self.busy and Path('/proc/device-tree/chosen/f8-cpu-trial').exists())
 def execute(self,args):
  if self.busy:return
  self.busy=True;self.status.setText('等待管理员验证并应用…');self.refresh()
  self.proc.start('/usr/bin/pkexec',['/usr/local/lib/f8-pro/performance-apply.py',*args])
 def finished(self,code,exitstatus):
  self.busy=False;stdout=bytes(self.proc.readAllStandardOutput()).decode(errors='replace');stderr=bytes(self.proc.readAllStandardError()).decode(errors='replace')
  try:
   d=json.loads(stdout);message='已应用；温控保护保持启用。' if code==0 and d.get('ok') else d.get('error','未能应用')
  except Exception:message='已取消或未获授权。' if code in [126,127] else ('未能应用：'+stderr[-350:])
  self.status.setText(message);self.refresh()
 def failed(self,error):
  if error==QProcess.ProcessError.FailedToStart:self.busy=False;self.status.setText('无法启动管理员验证程序');self.refresh()

if __name__=='__main__':
 app=QApplication(sys.argv);app.setStyleSheet('QPushButton,QComboBox {min-height:42px;} QGroupBox {font-size:16px;padding-top:12px;} QLabel {font-size:16px;}')
 w=Panel();w.show()
 if '--smoke' in sys.argv:
  def smoke():
   w.grab().save(str(Path.home()/'.cache/f8-performance-panel.png'))
   print(json.dumps({'cards':len(w.cards),'enabled':{k:snapshot(k)['enabled'] for k in DEVICES},'width':w.width(),'height':w.height()}));w.close()
  QTimer.singleShot(700,smoke)
 sys.exit(app.exec())
