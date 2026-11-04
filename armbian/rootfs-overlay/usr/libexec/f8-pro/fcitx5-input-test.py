#!/usr/bin/python3
from PyQt6.QtWidgets import QApplication,QWidget,QVBoxLayout,QLabel,QTextEdit,QHBoxLayout,QPushButton
from PyQt6.QtCore import Qt,QTimer
from PyQt6.QtGui import QInputMethodEvent
from pathlib import Path
import json,subprocess
class Editor(QTextEdit):
 def inputMethodEvent(self,e):
  if e.preeditString():status['preedit_seen']=True
  super().inputMethodEvent(e);save()
app=QApplication([]);status={'platform':app.platformName(),'preedit_seen':False,'chinese_committed':False}
path=Path.home()/'.local/state/f8-pro/fcitx5-input-test.json'
def save():
 status['chinese_committed']=any('\u4e00'<=c<='\u9fff' for c in edit.toPlainText())
 path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(status))
w=QWidget();w.setWindowTitle('F8 中文输入测试');lay=QVBoxLayout(w)
label=QLabel('点输入框弹出键盘，输入 nihao，再选择“你好”。\n可用 Ctrl+空格切换中英文；也请测试实体键盘。');label.setWordWrap(True);lay.addWidget(label)
edit=Editor();edit.setPlaceholderText('在这里输入测试文字（请勿输入密码）');edit.setMinimumHeight(100);edit.textChanged.connect(save);lay.addWidget(edit)
row=QHBoxLayout()
def choose(name):
 subprocess.run(['fcitx5-remote','-s',name],timeout=3);edit.setFocus()
for text,name in [('中文拼音','pinyin'),('英文','keyboard-us')]:
 b=QPushButton(text);b.clicked.connect(lambda checked=False,n=name:choose(n));row.addWidget(b)
b=QPushButton('显示键盘');b.clicked.connect(lambda:subprocess.Popen(['fcitx5-osk','force-show']));row.addWidget(b)
lay.addLayout(row);w.resize(680,300);w.show();QTimer.singleShot(500,edit.setFocus);save();app.exec()
