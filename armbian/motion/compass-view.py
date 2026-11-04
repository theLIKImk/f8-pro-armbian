#!/usr/bin/python3
"""Unprivileged AK8963 compass viewer with user-controlled, local calibration."""
import argparse,collections,datetime,json,math,os,queue,threading,time
from pathlib import Path
from PyQt6.QtCore import Qt,QPointF,QTimer
from PyQt6.QtGui import QColor,QFont,QPainter,QPen,QPolygonF
from PyQt6.QtWidgets import QApplication,QComboBox,QFrame,QHBoxLayout,QLabel,QMainWindow,QMessageBox,QPushButton,QScrollArea,QScroller,QVBoxLayout,QWidget

CONFIG=Path.home()/'.config/f8-pro/compass-calibration.json'

from sensor_fusion import flat_heading,magnetic_pose,MAG_MATRIX

def heading_degrees(corrected):return flat_heading(corrected)

def fit_flat_calibration(samples):
    """Fit the horizontal magnetic circle for a screen-up, flat-only compass."""
    if len(samples)<60:raise ValueError('继续平放转动：至少采集60组。')
    low=[min(v[i] for v in samples) for i in range(2)];high=[max(v[i] for v in samples) for i in range(2)]
    spans=[b-a for a,b in zip(low,high)]
    if min(spans)<20:raise ValueError('水平覆盖不足，请保持平放并转完一整圈。')
    if max(spans)>250:raise ValueError('磁场跨度异常，请移开磁性物品后重新采集。')
    origin=[(a+b)/2 for a,b in zip(low,high)];unit=sum(spans)/4
    rows=[]
    for v in samples:
        x,y=[(v[i]-origin[i])/unit for i in range(2)];rows.append(([2*x,2*y,1],x*x+y*y))
    matrix=[[sum(a[i]*a[j] for a,b in rows) for j in range(3)]+[sum(a[i]*b for a,b in rows)] for i in range(3)]
    for col in range(3):
        pivot=max(range(col,3),key=lambda r:abs(matrix[r][col]))
        if abs(matrix[pivot][col])<1e-7:raise ValueError('转动范围不足，请平放转完一整圈。')
        matrix[col],matrix[pivot]=matrix[pivot],matrix[col];divisor=matrix[col][col]
        matrix[col]=[v/divisor for v in matrix[col]]
        for row in range(3):
            if row!=col:
                ratio=matrix[row][col];matrix[row]=[a-ratio*b for a,b in zip(matrix[row],matrix[col])]
    cx,cy,d=[row[3] for row in matrix];r2=d+cx*cx+cy*cy
    if r2<=0:raise ValueError('圆拟合失败，请重新平放采集。')
    radius=math.sqrt(r2)*unit;offset=[origin[0]+cx*unit,origin[1]+cy*unit,0]
    residual=math.sqrt(sum((math.hypot(v[0]-offset[0],v[1]-offset[1])-radius)**2 for v in samples)/len(samples))
    angles=sorted(math.atan2(v[1]-offset[1],v[0]-offset[0]) for v in samples)
    gaps=[b-a for a,b in zip(angles,angles[1:])]+[angles[0]+2*math.pi-angles[-1]]
    if max(gaps)>math.radians(100):raise ValueError('还未覆盖完整一圈，请继续保持平放转动。')
    if not 5<radius<100 or residual/radius>.15 or min(spans)<radius:
        raise ValueError('磁场不一致，请远离手机与磁性物品，保持平放后重新采集。')
    return {'version':3,'offset_ut':offset,'scale':[1,1,1],'spans_ut':spans,'horizontal_radius_ut':radius,
            'fit_rms_ut':residual,'sample_count':len(samples),'method':'horizontal hard-iron circle fit; flat compass only; Z not calibrated',
            'time':datetime.datetime.now().astimezone().isoformat(),'north_reference_verified':False}

def fit_calibration(samples):
    """Fit a hard-iron sphere; reject disturbed fields and incomplete coverage."""
    if len(samples)<60:raise ValueError('至少采集60组，并转动、翻转覆盖三轴。')
    low=[min(v[i] for v in samples) for i in range(3)];high=[max(v[i] for v in samples) for i in range(3)]
    spans=[b-a for a,b in zip(low,high)]
    if min(spans)<20:raise ValueError('三轴覆盖不足，请继续翻转平板。')
    if max(spans)>250:raise ValueError('采样磁场跨度异常，请远离磁性物品，点击“重新采集”。')
    origin=[(a+b)/2 for a,b in zip(low,high)];unit=sum(spans)/6
    rows=[]
    for v in samples:
        q=[(v[i]-origin[i])/unit for i in range(3)]
        rows.append(([2*q[0],2*q[1],2*q[2],1],sum(n*n for n in q)))
    matrix=[[sum(a[i]*a[j] for a,b in rows) for j in range(4)]+[sum(a[i]*b for a,b in rows)] for i in range(4)]
    for col in range(4):
        pivot=max(range(col,4),key=lambda r:abs(matrix[r][col]))
        if abs(matrix[pivot][col])<1e-7:raise ValueError('采样方向不够完整，请翻转覆盖更多方向。')
        matrix[col],matrix[pivot]=matrix[pivot],matrix[col];divisor=matrix[col][col]
        matrix[col]=[v/divisor for v in matrix[col]]
        for row in range(4):
            if row!=col:
                ratio=matrix[row][col];matrix[row]=[a-ratio*b for a,b in zip(matrix[row],matrix[col])]
    solution=[row[4] for row in matrix];r2=solution[3]+sum(v*v for v in solution[:3])
    if r2<=0:raise ValueError('校准拟合失败，请重新采集。')
    radius=math.sqrt(r2)*unit;offset=[origin[i]+solution[i]*unit for i in range(3)]
    residual=math.sqrt(sum((math.sqrt(sum((v[i]-offset[i])**2 for i in range(3)))-radius)**2 for v in samples)/len(samples))
    if not 10<radius<120 or residual/radius>.15 or min(spans)<radius:
        raise ValueError('磁场一致性或覆盖不足，请移开手机、磁吸附件后重新完整采集。')
    return {'version':2,'offset_ut':offset,'scale':[1,1,1],'spans_ut':spans,'field_radius_ut':radius,
            'fit_rms_ut':residual,'sample_count':len(samples),'method':'least-squares hard-iron sphere fit; no soft-iron correction',
            'time':datetime.datetime.now().astimezone().isoformat(),'north_reference_verified':False}
def text(value,size=14,color='#e6eefb'):
    label=QLabel(value);label.setWordWrap(True);label.setStyleSheet(f'font-size:{size}px;color:{color};');return label

class Dial(QWidget):
    def __init__(self):
        super().__init__();self.heading=None;self.setMinimumHeight(260)
    def paintEvent(self,event):
        p=QPainter(self);p.setRenderHint(QPainter.RenderHint.Antialiasing)
        cx,cy=self.width()/2,self.height()/2;r=min(self.width(),self.height())*.40
        p.setPen(QPen(QColor('#304763'),2));p.setBrush(QColor('#111f33'));p.drawEllipse(QPointF(cx,cy),r,r)
        p.setPen(QColor('#a8bad0'));p.setFont(QFont('Sans Serif',13))
        # A rotating compass card: north label and north needle always agree.
        rotation=self.heading if self.heading is not None else 0
        for angle,word in [(0,'北 N'),(90,'东 E'),(180,'南 S'),(270,'西 W')]:
            theta=math.radians(angle-rotation);x=cx+math.sin(theta)*(r+18);y=cy-math.cos(theta)*(r+18)
            p.drawText(int(x)-22,int(y)+5,word)
        for angle in range(0,360,15):
            theta=math.radians(angle-rotation);p.setPen(QPen(QColor('#3c536e'),2))
            p.drawLine(QPointF(cx+math.sin(theta)*(r-9),cy-math.cos(theta)*(r-9)),QPointF(cx+math.sin(theta)*r,cy-math.cos(theta)*r))
        if self.heading is None:
            p.setPen(QColor('#90a2ba'));p.drawText(self.rect(),Qt.AlignmentFlag.AlignCenter,'完成校准后显示磁北估算');return
        p.setPen(Qt.PenStyle.NoPen);p.setBrush(QColor('#ffbf6b'))
        p.drawPolygon(QPolygonF([QPointF(cx,cy-r+15),QPointF(cx-6,cy-r+3),QPointF(cx+6,cy-r+3)]))
        p.translate(cx,cy);p.rotate(-self.heading)
        p.setPen(Qt.PenStyle.NoPen);p.setBrush(QColor('#67d8ef'))
        p.drawPolygon(QPolygonF([QPointF(0,-r*.8),QPointF(-14,18),QPointF(14,18)]))
        p.setBrush(QColor('#66758c'));p.drawPolygon(QPolygonF([QPointF(0,r*.65),QPointF(-14,18),QPointF(14,18)]))

class Reader:
    def __init__(self):
        self.stop=threading.Event();self.data=queue.Queue(maxsize=1)
        threading.Thread(target=self.run,daemon=True).start()
    def run(self):
        while not self.stop.is_set():
            sample={'time':datetime.datetime.now().astimezone().isoformat()}
            try:
                devices=[p for p in Path('/sys/bus/iio/devices').glob('iio:device*') if (p/'name').read_text().strip().lower()=='ak8963']
                if not devices:raise OSError('未找到 AK8963 IIO 设备')
                device=devices[0];raw=[];values=[]
                for axis in 'xyz':
                    n=int((device/f'in_magn_{axis}_raw').read_text());scale=float((device/f'in_magn_{axis}_scale').read_text())
                    raw.append(n);values.append(n*scale*100) # IIO gauss -> microtesla
                sample.update(device=str(device),raw=raw,ut=values)
                for imu in Path('/sys/bus/iio/devices').glob('iio:device*'):
                    if (imu/'name').read_text().strip()=='mpu6500':
                        a=[int((imu/f'in_accel_{axis}_raw').read_text()) for axis in 'xyz']
                        norm=math.sqrt(sum(v*v for v in a));sample['level']=bool(norm and a[2]/norm<-.92)
                        sample['flat_for_cal']=bool(norm and a[2]/norm<-.985);sample['accel_board']=[sum(row[i]*a[i] for i in range(3)) for row in ((0,-1,0),(-1,0,0),(0,0,-1))];break
            except (OSError,ValueError) as e:sample['error']=str(e)
            try:self.data.get_nowait()
            except queue.Empty:pass
            self.data.put_nowait(sample);self.stop.wait(.25)

class Window(QMainWindow):
    def __init__(self,three_axis=False):
        super().__init__();self.setWindowTitle('F8 指南针 · 三轴校准' if three_axis else 'F8 指南针测试');self.resize(720,830);self.setMinimumSize(500,450)
        self.cal=None;self.cal_problem='';self.fit_error='';self.collecting=False;self.samples=[];self.current=None;self.reader=Reader()
        try:
            c=json.loads(CONFIG.read_text());assert c['version'] in [1,2,3]
            if max(c.get('spans_ut',[0]))>250:raise ValueError('旧校准磁场跨度异常，已保留文件，请重新校准。')
            assert len(c['offset_ut'])==len(c['scale'])==3 and all(math.isfinite(v) for k in ['offset_ut','scale'] for v in c[k])
            assert all(.1<v<10 for v in c['scale']);self.cal=c
        except ValueError as e:self.cal_problem=str(e)
        except (OSError,AssertionError,KeyError,TypeError):pass
        host=QWidget();scroll=QScrollArea();scroll.setWidgetResizable(True);scroll.setWidget(host);QScroller.grabGesture(scroll.viewport(),QScroller.ScrollerGestureType.TouchGesture);self.setCentralWidget(scroll);layout=QVBoxLayout(host);layout.setContentsMargins(25,20,25,20);layout.setSpacing(12)
        layout.addWidget(text('F8 指南针测试',27));layout.addWidget(text('AK8963 · 磁场读数与用户校准',14,'#90a2ba'))
        self.status=text('正在读取罗盘…',15,'#ffbf6b');layout.addWidget(self.status)
        self.dial=Dial();layout.addWidget(self.dial,1)
        self.heading=text('待校准',30,'#67d8ef');self.heading.setAlignment(Qt.AlignmentFlag.AlignCenter);layout.addWidget(self.heading)
        self.axes=text('磁场 X / Y / Z：—',19);layout.addWidget(self.axes)
        self.norm=text('原始模长：—',13,'#90a2ba');layout.addWidget(self.norm)
        self.progress=text(self.cal_problem or ('已加载本机校准；指北方向仍待手机对照。' if self.cal else '点击“开始校准”，屏幕朝上保持平放，在原地缓慢水平转一整圈，约30秒。'),14);layout.addWidget(self.progress)
        layout.addWidget(text('以原生竖屏顶部为朝向，已按本次要求整体调转180°。平面校准仅平放；三轴校准后可倾斜读磁北。',13,'#90a2ba'))
        self.mode=QComboBox();self.mode.addItems(['平面校准（保持平放转一圈）','三轴校准（缓慢转动并翻转，启用倾斜补偿）']);self.mode.setCurrentIndex(1 if three_axis else 0);layout.addWidget(self.mode);self.mode.currentIndexChanged.connect(self.cancel_capture)
        controls=QHBoxLayout();self.start=QPushButton('开始校准');self.start.clicked.connect(self.begin);controls.addWidget(self.start)
        self.save=QPushButton('保存校准');self.save.setEnabled(False);self.save.clicked.connect(self.finish);controls.addWidget(self.save)
        reset=QPushButton('清除校准');reset.clicked.connect(self.reset);controls.addWidget(reset)
        close=QPushButton('关闭');close.clicked.connect(self.close);controls.addWidget(close);layout.addLayout(controls)
        self.setStyleSheet('QComboBox{color:#e6eefb;background:#21344f;padding:10px;} QComboBox QAbstractItemView{color:#e6eefb;background:#21344f;selection-background-color:#365b7e;} QWidget{background:#0b1422;} QLabel{background:transparent;} QPushButton{color:#e6eefb;background:#21344f;border:1px solid #355071;border-radius:8px;padding:13px 15px;font-size:14px;} QPushButton:disabled{color:#718298;} QPushButton:pressed{background:#355b7b;}')
        self.timer=QTimer(self);self.timer.timeout.connect(self.tick);self.timer.start(100)
    def cancel_capture(self):
        self.collecting=False;self.samples=[];self.save.setEnabled(False);self.start.setText('开始校准');self.progress.setText('校准方式已切换；原校准保持不变，点击开始后再采集。')
    def begin(self):
        self.collecting=True;self.samples=[];self.fit_error='';self.save.setEnabled(False);self.start.setText('重新采集');self.progress.setText('缓慢转动并翻转，覆盖XYZ三个方向；不要靠近磁性物品。' if self.mode.currentIndex()==1 else '屏幕朝上保持平放，原地水平转一整圈；保存按钮亮起后点击。')
    def spans(self):return [max(v[i] for v in self.samples)-min(v[i] for v in self.samples) for i in range(3)]
    def finish(self):
        try:
            cache=Path.home()/'.cache/f8-compass';cache.mkdir(parents=True,exist_ok=True)
            (cache/'last-calibration-attempt.json').write_text(json.dumps({'method':'three-axis-sphere' if self.mode.currentIndex()==1 else 'flat-circle','samples_ut':self.samples,'time':datetime.datetime.now().astimezone().isoformat()}))
        except OSError:pass
        try:calibration=(fit_calibration if self.mode.currentIndex()==1 else fit_flat_calibration)(self.samples)
        except ValueError as e:self.fit_error=str(e);self.progress.setText(self.fit_error);return
        try:
            CONFIG.parent.mkdir(parents=True,exist_ok=True)
            if CONFIG.exists():CONFIG.with_name('compass-calibration.backup-'+datetime.datetime.now().strftime('%Y%m%d-%H%M%S')+'.json').write_bytes(CONFIG.read_bytes())
            CONFIG.write_text(json.dumps(calibration,indent=2)+'\n')
        except OSError as e:QMessageBox.warning(self,'保存失败',str(e));return
        self.cal=calibration;self.collecting=False;self.mode.setEnabled(True);self.save.setEnabled(False);self.progress.setText('三轴校准已保存，倾斜补偿已启用；请对照手机检查。' if calibration['version']==2 else '平放校准已保存；仅用于平放指北，三轴校准后可倾斜读角度。')
    def reset(self):
        if QMessageBox.question(self,'清除校准','清除本机保存的指南针校准？')!=QMessageBox.StandardButton.Yes:return
        try:CONFIG.unlink(missing_ok=True)
        except OSError as e:QMessageBox.warning(self,'清除失败',str(e));return
        self.cal=None;self.collecting=False;self.save.setEnabled(False);self.progress.setText('已清除；请重新校准。')
    def tick(self):
        try:sample=self.reader.data.get_nowait()
        except queue.Empty:return
        self.current=sample
        if 'error' in sample:
            self.status.setText('读数无效：'+sample['error']);self.heading.setText('等待有效读数');self.dial.heading=None;self.dial.update();return
        v=sample['ut'];self.axes.setText('磁场 µT   X %+.1f   Y %+.1f   Z %+.1f'%tuple(v))
        self.norm.setText('未校准模长 %.1f µT（包含机身偏置）  ·  原始计数 %s'%(math.sqrt(sum(n*n for n in v)),sample['raw']))
        if self.collecting:
            if self.mode.currentIndex()==1 or sample.get('flat_for_cal'):self.samples.append(v)
            spans=self.spans() if self.samples else [0,0,0]
            ready=len(self.samples)>=60 and min(spans if self.mode.currentIndex()==1 else spans[:2])>=20
            self.save.setEnabled(ready)
            tip='可以尝试保存；请确认已经转完一整圈。' if ready else '继续平放转完一整圈。'
            if self.mode.currentIndex()==1:tip='XYZ跨度 %.1f / %.1f / %.1f µT；缓慢翻转覆盖三轴。'%tuple(spans)
            elif not sample.get('flat_for_cal'):tip='请屏幕朝上放平；倾斜时暂停计数。'
            if self.fit_error:tip+='\n上次保存提示：'+self.fit_error
            self.progress.setText('有效采样 %d/60 · 水平跨度 X %.1f / Y %.1f µT\n%s'%(len(self.samples),spans[0],spans[1],tip))
        self.status.setText('数据正常 · '+('屏幕接近平放' if sample.get('level') else '请将屏幕朝上平放后读角度'))
        heading=None
        if self.cal and (sample.get('level') or self.cal.get('version')==2):
            corrected=[(v[i]-self.cal['offset_ut'][i])*self.cal['scale'][i] for i in range(3)]
            mp=magnetic_pose(sample.get('accel_board'),corrected) if self.cal.get('version')==2 else None
            heading=mp['heading'] if mp else (heading_degrees(corrected) if sample.get('level') else None)
        self.dial.heading=heading;self.dial.update()
        direction=['北','东北','东','东南','南','西南','西','西北'][int((heading+22.5)//45)%8] if heading is not None else ''
        self.heading.setText(f'{heading:.0f}° {direction} · 磁北估算' if heading is not None else ('请平放' if self.cal else '待校准'))
        # Expose calibration progress for remote support without screen scraping.
        if time.monotonic()-getattr(self,'last_diagnostic',0)>1:
            self.last_diagnostic=time.monotonic()
            report={'time':sample['time'],'collecting':self.collecting,'sample_count':len(self.samples),
                    'spans_ut':self.spans() if self.samples else [],'progress':self.progress.text(),'status':self.status.text(),
                    'heading_degrees':heading,'compass_mount_revision':5,'heading_offset_deg':180,'calibration_version':self.cal.get('version') if self.cal else None,'capture_mode':self.mode.currentText(),'three_axis_selected':self.mode.currentIndex()==1}
            try:
                path=Path('/run/user')/str(os.getuid())/'f8-compass-status.json'
                temp=path.with_suffix('.tmp');temp.write_text(json.dumps(report,ensure_ascii=False));temp.replace(path)
            except OSError:pass
    def closeEvent(self,event):self.reader.stop.set();event.accept()

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--preview',type=Path);parser.add_argument('--three-axis',action='store_true');args=parser.parse_args()
    app=QApplication([]);app.setDesktopFileName('f8-compass');window=Window(args.three_axis);window.show()
    if args.preview:
        def preview():window.grab().save(str(args.preview));window.close();app.quit()
        QTimer.singleShot(2200,preview)
    return app.exec()
if __name__=='__main__':raise SystemExit(main())
