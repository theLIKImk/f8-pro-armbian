#!/usr/bin/python3
"""Touch-friendly first-login setup and an offline, reusable tablet guide."""
import json
import os
from pathlib import Path
import pwd
import subprocess
import sys
from PyQt6.QtCore import QThread,pyqtSignal,Qt,QTimer
from PyQt6.QtWidgets import (QApplication,QWizard,QWizardPage,QVBoxLayout,QLabel,
    QFormLayout,QLineEdit,QComboBox,QCheckBox,QPushButton,QTextBrowser,QMessageBox)

HELP='''<h2>欢迎使用 F8 平板</h2>
<p>Armbian · KDE Plasma · Wayland</p>
<p>轻触输入框即可使用屏幕键盘；屏幕旋转与触摸同步，按键提供短振反馈。</p>
<h3>连接与声音</h3><p>右下角网络图标连接 Wi-Fi；蓝牙设置可扫描并配对设备。USB-C 可直接接入已验证的 USB 2.0 U 盘，在文件管理器中安全移除后再拔出。系统音量控制扬声器与录音。</p>
<h3>相机</h3><p>打开「F8 相机（拍照录像）」并开始预览。使用 Kamoso 或网页相机前，在 F8 相机中开启「兼容中继」，保持其运行；网页请使用「Chromium（相机兼容）」入口并授权相机/麦克风。先停止预览再切换前后摄。</p>
<p>目前相机仅完成基础功能，默认 640×480 / 14fps；分辨率、色彩调校、对焦及 RAW 等设置仍待完善。F8 相机自身录像无声，Kamoso 和兼容浏览器已验证带声音录像。</p>
<h3>传感器与保护盖</h3><p>「传感器观察」提供姿态正方体、水平仪及实时读数；静放后可点「静置校零」。正方体表示相对姿态，长时间使用会漂移。指南针需远离磁吸保护套/音箱，先完成自己的校准，平放观察。</p>
<p>磁吸保护盖合盖熄屏、开盖亮屏；「F8 霍尔与振动测试」可切换联动并测试短振。合盖仅控制显示，不等同于休眠。虚拟键盘设置可关闭按键振动。</p>
<h3>当前测试版限制</h3><p>电池电量与充电采样尚未完成适配，显示数值可能不准确；高压 PD、系统休眠和 CPU 调频仍未验收。保持当前已验证的供电方式，勿据电量百分比判断续航。此版本仍需进行首次开机与重启恢复测试。</p>
<p>向导完成后可随时从应用菜单打开「F8 使用指南」重新查看这些说明。</p>'''

class Apply(QThread):
    done=pyqtSignal(object)
    def __init__(self,data):super().__init__();self.data=data
    def run(self):
        try:
            p=subprocess.run(['sudo','-n','/usr/local/lib/f8-pro/first-run-apply.py'],input=json.dumps(self.data).encode(),capture_output=True,timeout=240)
            result=json.loads(p.stdout)
            if p.returncode or not result.get('ok'):raise ValueError(result.get('error','设置失败。'))
            self.done.emit(result)
        except Exception as e:
            self.done.emit({'ok':False,'error':str(e) if isinstance(e,ValueError) else '设置暂时未能完成，请重试。'})
        finally:self.data.clear()

def page(title,text):
    p=QWizardPage();p.setTitle(title);p.box=QVBoxLayout(p)
    if text:
        l=QLabel(text);l.setWordWrap(True);p.box.addWidget(l)
    return p

class Account(QWizardPage):
    def __init__(self):
        super().__init__();self.setTitle('创建你的账户')
        box=QVBoxLayout(self);form=QFormLayout();box.addLayout(form)
        self.name=QLineEdit();self.name.setPlaceholderText('例如：f8user（小写字母开头）')
        self.full=QLineEdit();self.full.setPlaceholderText('可选')
        self.password=QLineEdit();self.password.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm=QLineEdit();self.confirm.setEchoMode(QLineEdit.EchoMode.Password)
        self.host=QLineEdit('f8-pad')
        for label,widget in [('用户名',self.name),('显示名称',self.full),('密码（至少8字符）',self.password),('再次输入密码',self.confirm),('设备名称',self.host)]:
            form.addRow(label,widget)
        self.auto=QCheckBox('以后开机自动登录此账户');box.addWidget(self.auto)
        warning=QLabel('选择自动登录后，可接触设备的人可直接进入桌面。');warning.setWordWrap(True);box.addWidget(warning)
        label=QLabel('账户可使用 sudo 管理系统；默认在登录界面输入密码。密码仅用于创建本机账户，不保存到向导记录。');label.setWordWrap(True);box.addWidget(label);box.addStretch()
    def validatePage(self):
        import re
        n=self.name.text();p=self.password.text();f=self.full.text();h=self.host.text()
        error=''
        if not re.fullmatch('[a-z][a-z0-9_-]{0,30}',n) or n in {'root','f8setup','f8test','f8gpu'}:error='请使用有效的新用户名。'
        elif not 8<=len(p)<=128 or any(ord(c)<32 or ord(c)==127 or c==':' for c in p):error='密码需要8至128个字符，不能包含冒号或控制字符。'
        elif p!=self.confirm.text():error='两次输入的密码不同。'
        elif len(f)>80 or any(ord(c)<32 or c in ':,' for c in f):error='显示名称不能含冒号、逗号或控制字符。'
        elif not re.fullmatch('[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?',h):error='请使用有效的设备名。'
        if error:QMessageBox.information(self,'检查账户信息',error);return False
        return True

class Wizard(QWizard):
    def __init__(self,preview=False,guide=False):
        super().__init__();self.preview=preview;self.guide=guide;self.busy=False;self.finished_setup=False
        self.setWindowTitle('F8 使用指南' if guide else 'F8 首次开机向导')
        screen=QApplication.primaryScreen().availableGeometry();self.resize(min(820,int(screen.width()*.94)),min(700,int(screen.height()*.90)))
        self.setWizardStyle(QWizard.WizardStyle.ModernStyle)
        self.setButtonText(QWizard.WizardButton.NextButton,'下一步 →');self.setButtonText(QWizard.WizardButton.BackButton,'← 上一步')
        self.setButtonText(QWizard.WizardButton.CancelButton,'稍后继续');self.setButtonText(QWizard.WizardButton.FinishButton,'完成设置')
        welcome=page('你好，欢迎来到 F8','接下来设置语言、账户和网络，然后进入你自己的 KDE 桌面。网络可以稍后连接，整个向导支持离线完成。' + ('\n这是预览模式，不会创建账户或修改系统。' if preview else ''))
        welcome.box.addStretch();self.addPage(welcome)
        if not guide:
            region=page('语言与时区','选择新账户的语言和本地时间。向导全程可使用屏幕键盘。')
            form=QFormLayout();self.locale=QComboBox()
            for label,code in [('简体中文','zh_CN.UTF-8'),('English','en_US.UTF-8'),('繁體中文','zh_TW.UTF-8')]:self.locale.addItem(label,code)
            self.tz=QComboBox();self.tz.setEditable(False)
            zones=['Asia/Hong_Kong','Asia/Shanghai','Asia/Taipei','UTC']
            tab=Path('/usr/share/zoneinfo/zone.tab')
            if tab.exists():zones+=sorted({x.split('\t')[2] for x in tab.read_text().splitlines() if x and not x.startswith('#')}-set(zones))
            self.tz.addItems(zones);form.addRow('语言',self.locale);form.addRow('时区',self.tz);region.box.addLayout(form);region.box.addStretch();self.addPage(region)
            self.account=Account();self.addPage(self.account)
            network=page('连接 Wi-Fi（可跳过）','点击下方按钮打开系统网络设置。网络密码由 NetworkManager 保存，向导不会读取。连接后返回此窗口继续；也可进入桌面后再连接。')
            b=QPushButton('打开 Wi-Fi 设置');b.clicked.connect(lambda:self.launch(['systemsettings','kcm_networkmanagement']));network.box.addWidget(b);network.box.addStretch();self.addPage(network)
        p=page('了解你的平板','');browser=QTextBrowser();browser.setHtml(HELP);browser.setOpenExternalLinks(False);p.box.addWidget(browser);self.addPage(p)
        self.end=page('准备完成','');self.summary=QLabel();self.summary.setWordWrap(True);self.end.box.addWidget(self.summary);self.end.box.addStretch();self.addPage(self.end)
        self.currentIdChanged.connect(self.update_summary)
    def launch(self,args):
        try:subprocess.Popen(args,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        except OSError:QMessageBox.information(self,'打开设置','暂时无法打开设置，可稍后从系统设置进入。')
    def update_summary(self,*_):
        if self.currentPage()!=self.end:return
        self.summary.setText('可随时从应用菜单重新打开本指南。' if self.guide else f'用户名：{self.account.name.text()}\n语言：{self.locale.currentText()}\n时区：{self.tz.currentText()}\n登录方式：'+('自动登录' if self.account.auto.isChecked() else '输入密码登录')+'\n\n点击“完成设置”保存；成功后点击“进入登录界面”，选择新账户登录。')
    def accept(self):
        if self.busy:return
        if self.guide or self.preview:return super().accept()
        if self.finished_setup:
            self.launch(['qdbus6','org.kde.Shutdown','/Shutdown','org.kde.Shutdown.logout']);return super().accept()
        self.busy=True
        for b in [QWizard.WizardButton.FinishButton,QWizard.WizardButton.BackButton,QWizard.WizardButton.CancelButton]:self.button(b).setEnabled(False)
        self.summary.setText('正在创建账户并保存设置，请稍候……')
        a=self.account
        data=dict(username=a.name.text(),fullname=a.full.text(),password=a.password.text(),locale=self.locale.currentData(),timezone=self.tz.currentText(),hostname=a.host.text(),autologin=a.auto.isChecked())
        self.worker=Apply(data);self.worker.done.connect(self.applied);self.worker.start()
    def applied(self,result):
        self.busy=False;self.button(QWizard.WizardButton.FinishButton).setEnabled(True)
        if result.get('ok'):
            self.finished_setup=True;self.account.password.clear();self.account.confirm.clear()
            self.summary.setText('设置已保存。点击下方按钮进入登录界面，然后使用刚创建的账户。\n\n若选择自动登录，也可重启后进入自己的桌面。')
            self.setButtonText(QWizard.WizardButton.FinishButton,'进入登录界面')
        else:
            self.summary.setText(result['error']);self.button(QWizard.WizardButton.BackButton).setEnabled(True);self.button(QWizard.WizardButton.CancelButton).setEnabled(True)
    def reject(self):
        if not self.busy:super().reject()
    def closeEvent(self,event):
        if self.busy:event.ignore()
        else:super().closeEvent(event)

def main():
    guide='--guide' in sys.argv;preview='--preview' in sys.argv
    if not guide and not preview and (pwd.getpwuid(os.getuid()).pw_name!='f8setup' or Path('/var/lib/f8-pro/first-run/complete.json').exists()):return 0
    app=QApplication(sys.argv);app.setStyle('Breeze');app.setFont(__import__('PyQt6.QtGui',fromlist=['QFont']).QFont('Noto Sans CJK SC',12))
    app.setStyleSheet('QPushButton { min-height: 40px; padding: 4px 14px; } QLineEdit,QComboBox { min-height: 36px; }')
    window=Wizard(preview,guide);window.show()
    if '--render-preview' in sys.argv:
        dest=Path(sys.argv[sys.argv.index('--render-preview')+1]);dest.mkdir(parents=True,exist_ok=True)
        def render():
            # Render every actual page, not just the welcome page.
            for i in window.pageIds():
                window.setStartId(i);window.restart();app.processEvents();window.grab().save(str(dest/f'page-{i}.png'))
            app.quit()
        QTimer.singleShot(500,render)
    return app.exec()

if __name__=='__main__':sys.exit(main())
