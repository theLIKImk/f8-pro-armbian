#!/usr/bin/python3
"""Qt input helper: request on stdin, response on stdout; never log entered text."""
import json,sys
from PyQt6.QtCore import Qt,QTimer
from PyQt6.QtWidgets import QApplication,QDialog,QDialogButtonBox,QLabel,QLineEdit,QPlainTextEdit,QVBoxLayout

demo='--demo' in sys.argv
request={'title':'输入测试','prompt':'请输入 F8测试abc，分别检查软键盘和实体键盘。','mode':'text'} if demo else json.loads(sys.stdin.buffer.read(1024*1024))
app=QApplication([sys.argv[0]])
dialog=QDialog();dialog.setWindowTitle('Phira · '+request.get('title','输入'));dialog.setMinimumWidth(420)
layout=QVBoxLayout(dialog);prompt=QLabel(request.get('prompt','请输入'));prompt.setTextFormat(Qt.TextFormat.PlainText);prompt.setWordWrap(True);layout.addWidget(prompt)
if request.get('mode')=='multiline':
 field=QPlainTextEdit();field.setPlainText(request.get('default',''));field.setMinimumHeight(120)
 if not request.get('auto_wrap',True):field.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
else:
 field=QLineEdit(request.get('default',''));field.setMinimumHeight(44)
 if request.get('mode')=='password':
  field.setEchoMode(QLineEdit.EchoMode.Password);field.setInputMethodHints(Qt.InputMethodHint.ImhSensitiveData|Qt.InputMethodHint.ImhHiddenText|Qt.InputMethodHint.ImhNoPredictiveText)
 else:field.setInputMethodHints(Qt.InputMethodHint.ImhNoAutoUppercase)
 field.returnPressed.connect(dialog.accept)
field.setAttribute(Qt.WidgetAttribute.WA_InputMethodEnabled,True);field.setAccessibleName(request.get('title','输入'));layout.addWidget(field)
buttons=QDialogButtonBox(QDialogButtonBox.StandardButton.Ok|QDialogButtonBox.StandardButton.Cancel)
buttons.button(QDialogButtonBox.StandardButton.Ok).setText(request.get('ok','确定'));buttons.button(QDialogButtonBox.StandardButton.Cancel).setText(request.get('cancel','取消'))
buttons.accepted.connect(dialog.accept);buttons.rejected.connect(dialog.reject);layout.addWidget(buttons)
dialog.setStyleSheet('QLineEdit,QPlainTextEdit,QLabel,QPushButton{font-size:18px;} QPushButton{min-height:40px;min-width:90px;}')
def focus():
 dialog.raise_();dialog.activateWindow();field.setFocus(Qt.FocusReason.OtherFocusReason);app.inputMethod().show()
QTimer.singleShot(150,focus)
accepted=dialog.exec()==QDialog.DialogCode.Accepted
text=(field.toPlainText() if isinstance(field,QPlainTextEdit) else field.text()) if accepted else ''
response={'accepted':accepted,'characters':len(text)} if demo else {'accepted':accepted,'text':text}
sys.stdout.write(json.dumps(response,ensure_ascii=False)+'\n');sys.stdout.flush()
