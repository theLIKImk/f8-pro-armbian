#!/usr/bin/python3
"""Native Wayland integer target slider with real IRQ telemetry and recovery UI."""
import json,math,sys,time
from pathlib import Path
from PyQt6.QtCore import QProcess,QTimer,Qt
from PyQt6.QtWidgets import QApplication,QHBoxLayout,QLabel,QPushButton,QSlider,QSpinBox,QVBoxLayout,QWidget
ROOT=Path('/usr/libexec/f8-pro/touch-rate-panel')
class Window(QWidget):
 def __init__(self):
  super().__init__();self.setWindowTitle('F8 触摸采样率');self.resize(640,480)
  self.meta=json.loads((ROOT/'module.json').read_text());self.mapping=json.loads((ROOT/'rate-map.json').read_text())['rates']
  layout=QVBoxLayout(self)
  note=QLabel('全局生效，仅用于本次启动。滑块选择目标频率，实际上报率在触摸时显示。');note.setWordWrap(True);layout.addWidget(note)
  self.current=QLabel();layout.addWidget(self.current)
  self.live=QLabel('当前上报：等待触摸');self.live.setStyleSheet('font-size:22px;');layout.addWidget(self.live)
  row=QHBoxLayout();row.addWidget(QLabel('目标采样率'))
  self.number=QSpinBox();self.number.setRange(60,120);self.number.setSingleStep(1);self.number.setSuffix(' Hz');self.number.setValue(68);self.number.setMinimumHeight(50);row.addWidget(self.number);layout.addLayout(row)
  self.slider=QSlider(Qt.Orientation.Horizontal);self.slider.setRange(60,120);self.slider.setSingleStep(1);self.slider.setPageStep(10);self.slider.setValue(68);self.slider.setTickInterval(10);self.slider.setTickPosition(QSlider.TickPosition.TicksBelow);self.slider.setMinimumHeight(65);layout.addWidget(self.slider)
  ticks=QHBoxLayout();ticks.addWidget(QLabel('60 Hz'));ticks.addStretch();ticks.addWidget(QLabel('120 Hz'));layout.addLayout(ticks)
  self.period=QLabel();layout.addWidget(self.period)
  warning=QLabel('高频档可能增加断触。应用后请试用并点“保留本次设置”；45秒未确认会自动恢复原版。');warning.setWordWrap(True);layout.addWidget(warning)
  row=QHBoxLayout();self.apply=QPushButton('应用');self.restore=QPushButton('恢复原版')
  for b in [self.apply,self.restore]:b.setMinimumHeight(54);row.addWidget(b)
  layout.addLayout(row);self.keep=QPushButton('保留本次设置');self.keep.setMinimumHeight(54);layout.addWidget(self.keep)
  self.status=QLabel('设置不会写入 BOOT，重启使用原版。');self.status.setWordWrap(True);layout.addWidget(self.status)
  self.proc=QProcess(self);self.proc.finished.connect(self.finished);self.proc.errorOccurred.connect(lambda _:self.status.setText('无法启动管理员验证。'))
  self.slider.valueChanged.connect(self.number.setValue);self.number.valueChanged.connect(self.slider.setValue);self.number.valueChanged.connect(self.selection)
  self.apply.clicked.connect(lambda:self.execute('apply',str(self.number.value())));self.restore.clicked.connect(lambda:self.execute('restore'));self.keep.clicked.connect(lambda:self.execute('keep'))
  self.sample=None;self.first=True;self.request=None;self.selection()
  self.timer=QTimer(self);self.timer.timeout.connect(self.refresh);self.timer.start(250);self.refresh()
 def selection(self):
  self.period.setText(f"对应时序值：{self.mapping[str(self.number.value())]['period']}（根据实测点估算）")
 def execute(self,*args):
  if self.proc.state()!=QProcess.ProcessState.NotRunning:return
  self.request=args[0];self.status.setText('等待管理员验证并应用设置…')
  self.proc.start('/usr/bin/pkexec',['/usr/libexec/f8-pro/touch-rate-control.py',*args]);self.refresh()
 def finished(self,code,_):
  raw=bytes(self.proc.readAllStandardOutput()).decode(errors='replace')
  try:
   result=json.loads(raw)
   if not result.get('ok'):self.status.setText('未应用：'+result.get('error','操作失败'))
   elif self.request=='apply':self.status.setText('已应用。请试用触摸，再保留本次设置。')
   elif self.request=='keep':self.status.setText('已保留到本次关机或重启；可随时恢复原版。')
   else:self.status.setText('已恢复原版触摸配置。')
  except ValueError:self.status.setText('操作未完成或管理员验证已取消。')
  self.refresh()
 def refresh(self):
  busy=self.proc.state()!=QProcess.ProcessState.NotRunning;params=Path('/sys/module/f8_gsl_shuping/parameters');v=Path('/sys/module/f8_gsl_shuping/srcversion')
  try:version=v.read_text().strip()
  except OSError:version=None
  original=version==self.meta['baseline_srcversion'];controlled=version==self.meta['srcversion'];known=original or controlled
  d={}
  try:
   d=json.loads(Path('/run/f8-touch-rate-control.json').read_text())
   if d.get('boot_id')!=Path('/proc/sys/kernel/random/boot_id').read_text().strip():d={}
  except (OSError,ValueError):pass
  if controlled:
   try:
    period=int((params/'period').read_text());count=int((params/'irq_count').read_text());now=time.monotonic()
    self.current.setText(f"当前目标：{d.get('target_hz','—')} Hz · 时序值 {period}")
    if self.sample is None or self.sample[0]!=period or count<self.sample[2]:self.sample=(period,now,count)
    elif now-self.sample[1]>=1:
     delta=count-self.sample[2];rate=delta/(now-self.sample[1]);self.sample=(period,now,count)
     self.live.setText(f'当前上报：{rate:.1f} 次/秒（触摸时观察）' if delta>=10 else '当前上报：等待连续触摸')
   except (OSError,ValueError):self.current.setText('正在切换触摸驱动…');self.sample=None
  elif original:
   self.current.setText('当前：原版触摸（已测约 68 Hz）');self.live.setText('当前上报：原版没有计数接口');self.sample=None
  else:self.current.setText('当前触摸驱动未就绪或版本未识别');self.sample=None
  if self.first:
   self.first=False
   if controlled and type(d.get('target_hz'))==int and 60<=d['target_hz']<=120:self.number.setValue(d['target_hz'])
  pending=controlled and d.get('stage')=='pending' and d.get('pending_until') is not None
  left=max(0,math.ceil(d['pending_until']-time.monotonic())) if pending else 0
  self.keep.setText(f'保留本次设置（{left} 秒后恢复）' if pending else '保留本次设置')
  self.keep.setEnabled(pending and left>0 and not busy)
  self.apply.setEnabled(known and not busy);self.restore.setEnabled(known and not busy)
  self.slider.setEnabled(not busy);self.number.setEnabled(not busy)

if __name__=='__main__':
 app=QApplication(sys.argv);w=Window();w.show();sys.exit(app.exec())
