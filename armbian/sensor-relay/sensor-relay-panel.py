#!/usr/bin/python3
import json,time,sys
from pathlib import Path
import dbus
from PyQt6.QtCore import QTimer,Qt
from PyQt6.QtWidgets import QApplication,QWidget,QVBoxLayout,QHBoxLayout,QLabel,QCheckBox,QSlider,QPushButton,QMessageBox
app=QApplication(sys.argv);w=QWidget();w.setWindowTitle('F8 传感器中继与自动亮度');w.resize(760,600)
box=QVBoxLayout(w);title=QLabel('传感器中继与自动亮度');title.setStyleSheet('font-size:25px');box.addWidget(title)
info=QLabel('中继在后台读取真实传感器；关闭本窗口仍可使用。\n标准 IIO：加速度／陀螺仪／校准磁场；会话 D-Bus：融合姿态、磁场、光照与接近。');info.setWordWrap(True);box.addWidget(info)
relay_on=QCheckBox('启用传感器中继（浏览器／应用）');box.addWidget(relay_on)
relay_note=QLabel('关闭后停止兼容数据输出；自动亮度独立控制。');relay_note.setWordWrap(True);box.addWidget(relay_note)
auto=QCheckBox('启用自动亮度');box.addWidget(auto);desc=QLabel('相对光照曲线，缓慢调节12%–90%；手动改亮度后暂停60秒。\n锁屏、合盖时暂停。环境光为原始计数，尚未标定lux。');desc.setWordWrap(True);box.addWidget(desc)
row=QHBoxLayout();row.addWidget(QLabel('亮度偏好'));slider=QSlider(Qt.Orientation.Horizontal);slider.setRange(-25,25);row.addWidget(slider);amount=QLabel('0%');row.addWidget(amount);box.addLayout(row)
status=QLabel('正在连接…');status.setWordWrap(True);status.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse);box.addWidget(status);box.addStretch()
notes=QLabel('浏览器页面须使用 HTTPS 并允许传感器。不同应用支持的接口不同。\n磁场需有效三轴校准；网页磁力计是否暴露取决于浏览器。完整九轴另通过 D-Bus／JSON 提供。');notes.setWordWrap(True);box.addWidget(notes)
proxy=None;updating=False

def connect():
 global proxy
 proxy=dbus.Interface(dbus.SessionBus().get_object('net.f8.Sensors','/net/f8/Sensors'),'net.f8.Sensors1')
def update():
 global updating,proxy
 try:
  if proxy is None:connect()
  settings=json.loads(str(proxy.GetSettings(timeout=1)));s=json.loads(str(proxy.GetSnapshot(timeout=1)));age=time.monotonic()-s.get('monotonic',0);updating=True
  relay_on.setChecked(bool(settings.get('relay_enabled',True)));auto.setChecked(bool(settings['auto_brightness']));
  if not slider.isSliderDown() and not bias_timer.isActive():slider.setValue(round(settings.get('brightness_bias_percent',0)))
  amount.setText(f'{slider.value():+d}%');updating=False
  opt=s.get('optical',{});b=s.get('brightness') or {};state='已关闭' if not settings.get('relay_enabled',True) else '在线' if s.get('online') and age<1 else '数据过期／等待传感器'
  status.setText(f'中继：{state} · 数据龄期 {age:.2f}秒\nIIO加速度／角速度：'+('已连接' if s.get('iio_feed_connected') else '尚未连接')+'\n九轴磁参考：'+('有效' if s.get('absolute_valid') else '等待有效三轴磁场校准')+f'\n环境光原始值：{opt.get("ambient_raw","—")} · 接近：'+('近' if opt.get('near') else '远' if opt.get('near') is False else '未标定')+f'\n当前亮度：{b.get("current_percent","—")}% · 手动暂停剩余 {b.get("manual_pause_seconds",0)}秒'+ ('\n亮度控制错误：'+b['error'] if b.get('error') else '')+ ('\n传感器错误：'+s['error'] if s.get('error') else ''))
 except Exception as e:proxy=None;updating=False;status.setText('服务尚未就绪：'+str(e))
def relay_toggle(v):
 if updating:return
 try:proxy.SetRelayEnabled(v,timeout=2)
 except Exception as e:QMessageBox.warning(w,'设置失败',str(e))
def toggle(v):
 if updating:return
 try:proxy.SetAutoBrightness(v,timeout=2)
 except Exception as e:QMessageBox.warning(w,'设置失败',str(e))
def bias():
 bias_timer.stop()
 if updating:return
 try:proxy.SetBrightnessBias(float(slider.value()),timeout=2)
 except Exception as e:QMessageBox.warning(w,'设置失败',str(e))
bias_timer=QTimer();bias_timer.setSingleShot(True);bias_timer.timeout.connect(bias)
def changed(v):
 amount.setText(f'{v:+d}%')
 if not updating:bias_timer.start(400)
relay_on.toggled.connect(relay_toggle);auto.toggled.connect(toggle);slider.valueChanged.connect(changed);slider.sliderReleased.connect(bias)
timer=QTimer();timer.timeout.connect(update);timer.start(1000);update();w.show();app.exec()
